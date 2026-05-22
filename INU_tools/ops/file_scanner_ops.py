# INU_tools.ops.file_scanner_ops
# Operators for the binary file linter — scan a folder, save report,
# reveal a result file in the OS file manager.
#
# Phase 1: COL only (DFF/TXD stubs in core/file_lint return []).

import os
import datetime
import bpy

from .. import T


def _wm_results(context):
    """Convenience accessor for the WindowManager-side results coll."""
    return context.window_manager.gtatools_scan_results


class GTATOOLS_OT_scan_files(bpy.types.Operator):
    """Сканировать выбранную папку на crash-prone паттерны в DFF/COL/TXD"""
    bl_idname = "gtatools.scan_files"
    bl_label = "INU: Scan Files"
    bl_options = {'REGISTER'}

    def execute(self, context):
        s = context.scene.inu_settings
        folder = bpy.path.abspath(s.gtatools_scan_dir) if s.gtatools_scan_dir else ""
        if not folder or not os.path.isdir(folder):
            self.report({'ERROR'}, T("Укажите существующую папку"))
            return {'CANCELLED'}

        if not (s.gtatools_scan_dff or s.gtatools_scan_col or s.gtatools_scan_txd):
            self.report({'ERROR'}, T("Включите хотя бы один тип файла (DFF/COL/TXD)"))
            return {'CANCELLED'}

        from ..core.file_lint import scan_folder

        wm = context.window_manager
        results = wm.gtatools_scan_results
        results.clear()
        wm.gtatools_scan_results_index = 0

        wm.progress_begin(0, 100)

        def _progress(i, n, path):
            if n > 0:
                wm.progress_update(int(i * 100 / n))

        profile = getattr(s, 'gtatools_lint_profile', 'STANDARD')
        from ..core import game_versions as gv
        game = gv.game_of_scene(context.scene)
        try:
            issues = scan_folder(
                folder,
                scan_dff=s.gtatools_scan_dff,
                scan_col=s.gtatools_scan_col,
                scan_txd=s.gtatools_scan_txd,
                recursive=s.gtatools_scan_recursive,
                progress_cb=_progress,
                profile=profile,
                game=game,
            )
        finally:
            wm.progress_end()

        for iss in issues:
            item = results.add()
            item.severity = iss.severity
            item.code = iss.code
            item.file = iss.file
            item.where = iss.where
            item.message = iss.message

        n_err = sum(1 for x in issues if x.severity == 'ERROR')
        n_warn = sum(1 for x in issues if x.severity == 'WARN')
        n_info = sum(1 for x in issues if x.severity == 'INFO')

        if not issues:
            self.report({'INFO'}, T("Скан завершён: проблем не найдено"))
        else:
            self.report({'INFO'},
                f"{T('Скан завершён')}: {n_err} ERROR, {n_warn} WARN, {n_info} INFO")
        return {'FINISHED'}


def _resolve_report_dir(context):
    """Return (path, error_message). path is None when error_message is set."""
    s = context.scene.inu_settings
    target = s.gtatools_scan_report_target

    if target == 'BLEND':
        if not bpy.data.filepath:
            return None, T("Сцена не сохранена — сохраните .blend или выберите другую папку для отчёта")
        return os.path.dirname(bpy.data.filepath), None

    if target == 'SCAN':
        scan_dir = bpy.path.abspath(s.gtatools_scan_dir) if s.gtatools_scan_dir else ""
        if not scan_dir or not os.path.isdir(scan_dir):
            return None, T("Папка скана не задана — выберите .blend или свою папку")
        return scan_dir, None

    if target == 'CUSTOM':
        custom = bpy.path.abspath(s.gtatools_scan_report_custom_path) if s.gtatools_scan_report_custom_path else ""
        if not custom or not os.path.isdir(custom):
            return None, T("Своя папка для отчёта не задана или не существует")
        return custom, None

    return None, T("Неизвестный target для отчёта")


class GTATOOLS_OT_scan_save_report(bpy.types.Operator):
    """Сохранить результат скана в .txt"""
    bl_idname = "gtatools.scan_save_report"
    bl_label = "INU: Save Scan Report"
    bl_options = {'REGISTER'}

    def execute(self, context):
        results = _wm_results(context)
        if not results:
            self.report({'ERROR'}, T("Нет результатов для сохранения — сначала запустите скан"))
            return {'CANCELLED'}

        report_dir, err = _resolve_report_dir(context)
        if err:
            self.report({'ERROR'}, err)
            return {'CANCELLED'}

        ts = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_path = os.path.join(report_dir, f"inu_lint_{ts}.txt")

        n_err = sum(1 for x in results if x.severity == 'ERROR')
        n_warn = sum(1 for x in results if x.severity == 'WARN')
        n_info = sum(1 for x in results if x.severity == 'INFO')

        scan_dir = bpy.path.abspath(context.scene.inu_settings.gtatools_scan_dir)
        try:
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(f"INU Tools — Binary File Lint Report\n")
                f.write(f"Generated: {ts}\n")
                f.write(f"Scanned:   {scan_dir}\n")
                f.write(f"Recursive: {context.scene.inu_settings.gtatools_scan_recursive}\n")
                f.write(f"Issues:    {n_err} ERROR, {n_warn} WARN, {n_info} INFO\n")
                f.write("=" * 78 + "\n\n")
                for it in results:
                    loc = f" {it.where}" if it.where else ""
                    f.write(f"[{it.severity}] {it.code}\n")
                    f.write(f"  file:    {it.file}\n")
                    if it.where:
                        f.write(f"  where:   {it.where}\n")
                    f.write(f"  message: {it.message}\n\n")
        except OSError as e:
            self.report({'ERROR'}, f"{e.__class__.__name__}: {e}")
            return {'CANCELLED'}

        self.report({'INFO'}, f"{T('Отчёт сохранён:')} {out_path}")
        return {'FINISHED'}


class GTATOOLS_OT_scan_reveal_file(bpy.types.Operator):
    """Открыть папку файла в Проводнике"""
    bl_idname = "gtatools.scan_reveal_file"
    bl_label = "INU: Reveal Scan File"
    bl_options = {'REGISTER'}

    def execute(self, context):
        results = _wm_results(context)
        idx = context.window_manager.gtatools_scan_results_index
        if idx < 0 or idx >= len(results):
            self.report({'ERROR'}, T("Нет выбранной строки"))
            return {'CANCELLED'}

        path = results[idx].file
        if not os.path.exists(path):
            self.report({'ERROR'}, f"{T('Файл не найден:')} {path}")
            return {'CANCELLED'}

        # os.startfile is Windows-only; on other platforms fall back.
        try:
            if hasattr(os, 'startfile'):
                os.startfile(os.path.dirname(path))
            else:
                import subprocess, sys
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.Popen([opener, os.path.dirname(path)])
        except Exception as e:
            self.report({'ERROR'}, f"{e.__class__.__name__}: {e}")
            return {'CANCELLED'}
        return {'FINISHED'}


class GTATOOLS_OT_scan_clear(bpy.types.Operator):
    """Очистить список результатов"""
    bl_idname = "gtatools.scan_clear"
    bl_label = "INU: Clear Scan Results"
    bl_options = {'REGISTER'}

    def execute(self, context):
        wm = context.window_manager
        wm.gtatools_scan_results.clear()
        wm.gtatools_scan_results_index = 0
        return {'FINISHED'}


classes = (
    GTATOOLS_OT_scan_files,
    GTATOOLS_OT_scan_save_report,
    GTATOOLS_OT_scan_reveal_file,
    GTATOOLS_OT_scan_clear,
)
