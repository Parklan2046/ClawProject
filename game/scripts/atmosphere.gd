class_name WuxiaAtmosphere
extends Control

var reduce_motion := false
var elapsed := 0.0
var motes: Array[Dictionary] = []
var rng := RandomNumberGenerator.new()

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	rng.seed = 722026
	for i in 28:
		motes.append({
			"x": rng.randf(),
			"y": rng.randf(),
			"r": rng.randf_range(1.0, 2.8),
			"s": rng.randf_range(0.004, 0.013),
			"p": rng.randf_range(0.0, TAU)
		})
	set_process(not reduce_motion)
	queue_redraw()

func _process(delta: float) -> void:
	elapsed += delta
	for mote in motes:
		mote.y = fposmod(float(mote.y) - float(mote.s) * delta, 1.04)
	queue_redraw()

func _draw() -> void:
	var s := size
	if s.x <= 0.0 or s.y <= 0.0:
		return
	draw_rect(Rect2(Vector2.ZERO, s), Color("#090b0e"), true)
	var horizon := s.y * 0.58
	for i in 14:
		var t := float(i) / 13.0
		var alpha := lerpf(0.04, 0.34, t)
		draw_rect(
			Rect2(0.0, horizon + t * s.y * 0.42, s.x, s.y * 0.035 + 2.0),
			Color(0.03, 0.035, 0.045, alpha),
			true
		)
	var drift := 0.0 if reduce_motion else sin(elapsed * 0.12) * s.x * 0.025
	draw_set_transform(Vector2(drift, 0.0))
	draw_colored_polygon(PackedVector2Array([
		Vector2(-s.x * 0.08, s.y * 0.43),
		Vector2(s.x * 0.38, s.y * 0.35),
		Vector2(s.x * 0.74, s.y * 0.46),
		Vector2(s.x * 1.08, s.y * 0.39),
		Vector2(s.x * 1.08, s.y * 0.58),
		Vector2(s.x * 0.52, s.y * 0.53),
		Vector2(-s.x * 0.08, s.y * 0.62)
	]), Color(0.62, 0.65, 0.68, 0.045))
	draw_set_transform(Vector2.ZERO)
	for mote in motes:
		var pulse := 0.72 if reduce_motion else 0.55 + sin(elapsed * 1.2 + float(mote.p)) * 0.17
		var pos := Vector2(float(mote.x) * s.x, float(mote.y) * s.y)
		draw_circle(pos, float(mote.r), Color(0.76, 0.25, 0.20, pulse))

