/* nanosvg_rasterize — minimal CLI that uses the same nanosvg lib
 * Blender ships, rasterises an SVG at requested width/height, and
 * dumps raw RGBA bytes to stdout for Python to wrap into a PNG.
 *
 * Usage:  nanosvg_rasterize <svg_path> <width> <height>
 * Output: width * height * 4 bytes RGBA on stdout (binary).
 */

#define NANOSVG_IMPLEMENTATION
#define NANOSVGRAST_IMPLEMENTATION
#include "nanosvg.h"
#include "nanosvgrast.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <io.h>
#include <fcntl.h>

int main(int argc, char* argv[]) {
    if (argc != 4) {
        fprintf(stderr, "Usage: %s <svg_path> <width> <height>\n", argv[0]);
        return 1;
    }
    const char* svg_path = argv[1];
    int out_w = atoi(argv[2]);
    int out_h = atoi(argv[3]);
    if (out_w <= 0 || out_h <= 0) {
        fprintf(stderr, "Bad width/height: %s %s\n", argv[2], argv[3]);
        return 1;
    }

    NSVGimage* image = nsvgParseFromFile(svg_path, "px", 96.0f);
    if (image == NULL) {
        fprintf(stderr, "Failed to parse SVG: %s\n", svg_path);
        return 1;
    }
    if (image->width <= 0 || image->height <= 0) {
        fprintf(stderr, "Empty SVG image\n");
        nsvgDelete(image);
        return 1;
    }

    NSVGrasterizer* rast = nsvgCreateRasterizer();
    if (rast == NULL) {
        nsvgDelete(image);
        fprintf(stderr, "Failed to create rasterizer\n");
        return 1;
    }

    float scale = (float)out_w / image->width;
    /* If non-square SVG vs output, just use width scale (Blender icons
     * are square so it doesn't matter). */

    unsigned char* pixels = (unsigned char*)malloc((size_t)out_w * out_h * 4);
    if (pixels == NULL) {
        nsvgDeleteRasterizer(rast);
        nsvgDelete(image);
        return 1;
    }
    memset(pixels, 0, (size_t)out_w * out_h * 4);

    nsvgRasterize(rast, image, 0.0f, 0.0f, scale,
                  pixels, out_w, out_h, out_w * 4);

    _setmode(_fileno(stdout), _O_BINARY);
    fwrite(pixels, 1, (size_t)out_w * out_h * 4, stdout);

    free(pixels);
    nsvgDeleteRasterizer(rast);
    nsvgDelete(image);
    return 0;
}
