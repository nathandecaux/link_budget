import { XYGlyph, XYGlyphView, XYGlyphData } from "./xy_glyph";
import { LineVector, FillVector, HatchVector } from "../../core/property_mixins";
import { Line, Fill, Hatch } from "../../core/visuals";
import { Arrayable, Area } from "../../core/types";
import { Context2d } from "../../core/util/canvas";
import * as p from "../../core/properties";
export interface PatchData extends XYGlyphData {
}
export interface PatchView extends PatchData {
}
export declare class PatchView extends XYGlyphView {
    model: Patch;
    visuals: Patch.Visuals;
    protected _inner_loop(ctx: Context2d, indices: number[], sx: Arrayable<number>, sy: Arrayable<number>, func: (this: Context2d) => void): void;
    protected _render(ctx: Context2d, indices: number[], { sx, sy }: PatchData): void;
    draw_legend_for_index(ctx: Context2d, bbox: Area, index: number): void;
}
export declare namespace Patch {
    type Attrs = p.AttrsOf<Props>;
    type Props = XYGlyph.Props & LineVector & FillVector & HatchVector;
    type Visuals = XYGlyph.Visuals & {
        line: Line;
        fill: Fill;
        hatch: Hatch;
    };
}
export interface Patch extends Patch.Attrs {
}
export declare class Patch extends XYGlyph {
    properties: Patch.Props;
    constructor(attrs?: Partial<Patch.Attrs>);
    static initClass(): void;
}
