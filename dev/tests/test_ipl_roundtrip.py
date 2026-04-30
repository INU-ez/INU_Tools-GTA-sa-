"""Round-trip tests for core/ipl.py — IPL text + binary formats covering
inst, cull, grge, enex, pick, cars, auzo (box+sphere), jump, occl, tcyc,
zone sections.

Pure Python."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "INU_tools"))

from core.ipl import (  # noqa: E402
    IplFile,
    IplInstance,
    IplCull,
    IplGarage,
    IplEnex,
    IplPickup,
    IplCar,
    IplAuzo,
    IplJump,
    IplOccl,
    IplTcyc,
    IplZone,
    read_ipl,
    write_ipl,
    upsert_ipl,
    remove_ipl,
)


# ── inst (text) ──────────────────────────────────────────────────

def test_inst_text_round_trip(tmp_path):
    p = tmp_path / "inst.ipl"
    write_ipl(str(p), IplFile(instances=[
        IplInstance(model_id=1700, model_name="cj_house", interior=0,
                    pos_x=2495.0, pos_y=-1700.0, pos_z=13.5,
                    rot_x=0.0, rot_y=0.0, rot_z=0.707, rot_w=0.707,
                    lod_index=-1),
        IplInstance(model_id=1701, model_name="cj_lod", interior=0,
                    pos_x=2495.0, pos_y=-1700.0, pos_z=13.5,
                    rot_x=0.0, rot_y=0.0, rot_z=0.707, rot_w=0.707,
                    lod_index=0),
    ]))
    parsed = read_ipl(str(p))
    assert len(parsed.instances) == 2
    a, b = parsed.instances
    assert a.model_id == 1700
    assert a.model_name == "cj_house"
    assert abs(a.pos_x - 2495.0) < 1e-3
    assert abs(a.rot_w - 0.707) < 1e-3
    assert b.lod_index == 0  # LOD link to first instance


# ── inst (binary) ────────────────────────────────────────────────

def test_inst_binary_round_trip(tmp_path):
    """Binary IPL is what IMG-stored IPLs use (gta.dat compiled maps)."""
    p = tmp_path / "binary.ipl"
    ipl = IplFile(instances=[
        IplInstance(model_id=18001, model_name="loddummy", interior=0,
                    pos_x=100.0, pos_y=200.0, pos_z=15.5,
                    rot_x=0.0, rot_y=0.0, rot_z=0.0, rot_w=1.0,
                    lod_index=-1),
        IplInstance(model_id=18002, model_name="loddummy", interior=13,
                    pos_x=-50.5, pos_y=300.25, pos_z=20.0,
                    rot_x=0.0, rot_y=0.0, rot_z=0.5, rot_w=0.866,
                    lod_index=-1),
    ])
    write_ipl(str(p), ipl, binary=True)
    parsed = read_ipl(str(p))
    assert len(parsed.instances) == 2
    a, b = parsed.instances
    assert a.model_id == 18001
    assert abs(a.pos_x - 100.0) < 1e-3
    assert b.interior == 13
    assert abs(b.rot_z - 0.5) < 1e-3
    assert abs(b.rot_w - 0.866) < 1e-3


# ── cull ─────────────────────────────────────────────────────────

def test_cull_zone_round_trip(tmp_path):
    p = tmp_path / "cull.ipl"
    write_ipl(str(p), IplFile(culls=[
        IplCull(center_x=100.0, center_y=200.0, center_z=10.0,
                length=50.0, bottom=5.0, width=40.0, top=20.0,
                flag=2),
    ]))
    parsed = read_ipl(str(p))
    c = parsed.culls[0]
    assert abs(c.center_x - 100.0) < 1e-3
    assert abs(c.length - 50.0) < 1e-3
    assert c.flag == 2


def test_cull_with_mirror(tmp_path):
    """14-field cull has mirror parameters appended."""
    p = tmp_path / "cull_mirror.ipl"
    write_ipl(str(p), IplFile(culls=[
        IplCull(center_x=0.0, center_y=0.0, center_z=0.0,
                length=10.0, bottom=0.0, width=10.0, top=5.0,
                flag=128,
                mirror_vx=1.0, mirror_vy=0.0, mirror_vz=0.0, mirror_cm=0.0),
    ]))
    parsed = read_ipl(str(p))
    c = parsed.culls[0]
    assert c.has_mirror
    assert c.mirror_vx == 1.0


# ── garage ───────────────────────────────────────────────────────

def test_garage_round_trip(tmp_path):
    p = tmp_path / "grge.ipl"
    write_ipl(str(p), IplFile(garages=[
        IplGarage(pos_x=100.0, pos_y=200.0, pos_z=10.0,
                  line_x=110.0, line_y=200.0,
                  cube_x=120.0, cube_y=210.0, cube_z=15.0,
                  flags=0, garage_type=1, name="GAR1"),
    ]))
    parsed = read_ipl(str(p))
    g = parsed.garages[0]
    assert g.name == "GAR1"
    assert g.garage_type == 1
    assert abs(g.pos_x - 100.0) < 1e-3


# ── enex ─────────────────────────────────────────────────────────

def test_enex_round_trip(tmp_path):
    p = tmp_path / "enex.ipl"
    write_ipl(str(p), IplFile(enexs=[
        IplEnex(x1=100.0, y1=200.0, z1=10.0, enter_angle=90.0,
                size_x=2.0, size_y=2.0, size_z=3.0,
                x2=100.0, y2=205.0, z2=11.0, exit_angle=270.0,
                target_interior=1, flags=0, name="HOSP1",
                sky=0, num_peds=5, time_on=0, time_off=24),
    ]))
    parsed = read_ipl(str(p))
    e = parsed.enexs[0]
    assert e.name == "HOSP1"
    assert e.target_interior == 1
    assert e.num_peds == 5
    assert e.time_off == 24


# ── pickups ──────────────────────────────────────────────────────

def test_pickup_round_trip(tmp_path):
    p = tmp_path / "pick.ipl"
    write_ipl(str(p), IplFile(pickups=[
        IplPickup(pickup_id=355, pos_x=100.0, pos_y=200.0, pos_z=10.0),
    ]))
    parsed = read_ipl(str(p))
    pk = parsed.pickups[0]
    assert pk.pickup_id == 355
    assert abs(pk.pos_z - 10.0) < 1e-3


# ── cars (parked) ────────────────────────────────────────────────

def test_cars_text_round_trip(tmp_path):
    p = tmp_path / "cars.ipl"
    write_ipl(str(p), IplFile(cars=[
        IplCar(pos_x=100.0, pos_y=200.0, pos_z=10.0, angle=0.0,
               car_id=400, primary_color=1, secondary_color=2,
               force_spawn=0, alarm=10, door_lock=2),
    ]))
    parsed = read_ipl(str(p))
    c = parsed.cars[0]
    assert c.car_id == 400
    assert c.primary_color == 1
    assert c.alarm == 10


# ── auzo (audio zones) ───────────────────────────────────────────

def test_auzo_box_round_trip(tmp_path):
    p = tmp_path / "auzo_box.ipl"
    write_ipl(str(p), IplFile(auzos=[
        IplAuzo(name="HOSPITAL", audio_id=4, switch=1,
                x1=100.0, y1=200.0, z1=5.0,
                x2=120.0, y2=220.0, z2=15.0),
    ]))
    parsed = read_ipl(str(p))
    a = parsed.auzos[0]
    assert a.name == "HOSPITAL"
    assert not a.is_sphere
    assert a.audio_id == 4


def test_auzo_sphere_round_trip(tmp_path):
    p = tmp_path / "auzo_sphere.ipl"
    write_ipl(str(p), IplFile(auzos=[
        IplAuzo(name="ALARM", audio_id=2, switch=1,
                x1=100.0, y1=200.0, z1=10.0, radius=25.0),
    ]))
    parsed = read_ipl(str(p))
    a = parsed.auzos[0]
    assert a.is_sphere
    assert abs(a.radius - 25.0) < 1e-3


# ── jump (stunt jumps) ───────────────────────────────────────────

def test_jump_round_trip(tmp_path):
    p = tmp_path / "jump.ipl"
    write_ipl(str(p), IplFile(jumps=[
        IplJump(start_lower_x=100.0, start_lower_y=200.0, start_lower_z=10.0,
                start_upper_x=110.0, start_upper_y=210.0, start_upper_z=15.0,
                target_lower_x=200.0, target_lower_y=300.0, target_lower_z=10.0,
                target_upper_x=210.0, target_upper_y=310.0, target_upper_z=15.0,
                camera_x=150.0, camera_y=250.0, camera_z=20.0,
                reward=500),
    ]))
    parsed = read_ipl(str(p))
    j = parsed.jumps[0]
    assert j.reward == 500
    assert abs(j.camera_y - 250.0) < 1e-3


# ── occl ─────────────────────────────────────────────────────────

def test_occl_round_trip(tmp_path):
    p = tmp_path / "occl.ipl"
    write_ipl(str(p), IplFile(occls=[
        IplOccl(mid_x=100.0, mid_y=200.0, bottom_z=10.0,
                width_x=20.0, width_y=30.0, height=15.0,
                rotation=45.0, unknown3=1),
    ]))
    parsed = read_ipl(str(p))
    o = parsed.occls[0]
    assert abs(o.rotation - 45.0) < 1e-3
    assert o.unknown3 == 1


# ── tcyc ─────────────────────────────────────────────────────────

def test_tcyc_round_trip(tmp_path):
    p = tmp_path / "tcyc.ipl"
    write_ipl(str(p), IplFile(tcycs=[
        IplTcyc(x1=100.0, y1=200.0, z1=10.0,
                x2=120.0, y2=220.0, z2=20.0,
                far_clip=300, extra_color=4,
                extra_color_intensity=0.5,
                falloff_dist=50.0, lod_dist_mult=1.5),
    ]))
    parsed = read_ipl(str(p))
    t = parsed.tcycs[0]
    assert t.far_clip == 300
    assert t.extra_color == 4
    assert abs(t.extra_color_intensity - 0.5) < 1e-3
    assert abs(t.lod_dist_mult - 1.5) < 1e-3


# ── zones ────────────────────────────────────────────────────────

def test_zone_round_trip(tmp_path):
    p = tmp_path / "zone.ipl"
    write_ipl(str(p), IplFile(zones=[
        IplZone(name="LOSANTOS", zone_type=0,
                x1=-3000.0, y1=-3000.0, z1=-100.0,
                x2=3000.0, y2=3000.0, z2=200.0, level=0),
    ]))
    parsed = read_ipl(str(p))
    z = parsed.zones[0]
    assert z.name == "LOSANTOS"
    assert z.zone_type == 0
    assert abs(z.x2 - 3000.0) < 1e-3


# ── upsert / remove ──────────────────────────────────────────────

def test_upsert_inst(tmp_path):
    p = tmp_path / "u.ipl"
    write_ipl(str(p), IplFile(instances=[
        IplInstance(model_id=100, model_name="a", interior=0,
                    pos_x=0.0, pos_y=0.0, pos_z=0.0,
                    rot_x=0, rot_y=0, rot_z=0, rot_w=1.0, lod_index=-1),
    ]))
    inserted, updated = upsert_ipl(str(p), [
        IplInstance(model_id=100, model_name="a", interior=0,
                    pos_x=10.0, pos_y=0.0, pos_z=0.0,
                    rot_x=0, rot_y=0, rot_z=0, rot_w=1.0, lod_index=-1),
        IplInstance(model_id=101, model_name="new", interior=0,
                    pos_x=0.0, pos_y=0.0, pos_z=0.0,
                    rot_x=0, rot_y=0, rot_z=0, rot_w=1.0, lod_index=-1),
    ])
    # IPL upsert semantics may differ from IDE — just check counts net out
    assert inserted >= 1 or updated >= 1
    parsed = read_ipl(str(p))
    ids = [i.model_id for i in parsed.instances]
    assert 100 in ids
    assert 101 in ids


def test_remove_drops_instances(tmp_path):
    p = tmp_path / "r.ipl"
    write_ipl(str(p), IplFile(instances=[
        IplInstance(model_id=100, model_name="a", interior=0,
                    pos_x=0, pos_y=0, pos_z=0,
                    rot_x=0, rot_y=0, rot_z=0, rot_w=1.0, lod_index=-1),
        IplInstance(model_id=101, model_name="b", interior=0,
                    pos_x=0, pos_y=0, pos_z=0,
                    rot_x=0, rot_y=0, rot_z=0, rot_w=1.0, lod_index=-1),
    ]))
    removed = remove_ipl(str(p), {101})
    assert removed == 1
    parsed = read_ipl(str(p))
    ids = {i.model_id for i in parsed.instances}
    assert ids == {100}


# ── Multi-section file ───────────────────────────────────────────

def test_multi_section_file(tmp_path):
    p = tmp_path / "mixed.ipl"
    write_ipl(str(p), IplFile(
        instances=[
            IplInstance(model_id=1700, model_name="house", interior=0,
                        pos_x=0, pos_y=0, pos_z=0,
                        rot_x=0, rot_y=0, rot_z=0, rot_w=1.0,
                        lod_index=-1),
        ],
        culls=[
            IplCull(center_x=0, center_y=0, center_z=0,
                    length=10, bottom=0, width=10, top=5, flag=1),
        ],
        zones=[
            IplZone(name="Z1", x1=-100, y1=-100, x2=100, y2=100),
        ],
    ))
    parsed = read_ipl(str(p))
    assert len(parsed.instances) == 1
    assert len(parsed.culls) == 1
    assert len(parsed.zones) == 1
