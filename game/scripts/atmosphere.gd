class_name WuxiaAtmosphere
extends Control

var reduce_motion := false
var elapsed := 0.0
var motes: Array[Dictionary] = []
var walkers: Array[Dictionary] = []
var rng := RandomNumberGenerator.new()

const LANTERNS := [
	Vector2(0.055, 0.555),
	Vector2(0.140, 0.420),
	Vector2(0.285, 0.475),
	Vector2(0.395, 0.560),
	Vector2(0.490, 0.565),
	Vector2(0.940, 0.535)
]

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	rng.seed = 722026
	for i in 34:
		motes.append({
			"x": rng.randf(),
			"y": rng.randf_range(0.28, 1.0),
			"r": rng.randf_range(0.8, 2.2),
			"s": rng.randf_range(0.004, 0.014),
			"p": rng.randf_range(0.0, TAU)
		})
	walkers = [
		{"phase": 0.08, "lane": -0.62, "speed": 0.018, "color": Color("#171b20")},
		{"phase": 0.34, "lane": 0.48, "speed": 0.013, "color": Color("#21191b")},
		{"phase": 0.61, "lane": -0.18, "speed": 0.010, "color": Color("#18201d")},
		{"phase": 0.82, "lane": 0.72, "speed": 0.008, "color": Color("#1b1922")}
	]
	set_process(not reduce_motion)
	queue_redraw()

func _process(delta: float) -> void:
	elapsed += delta
	for mote in motes:
		mote.y = fposmod(float(mote.y) - float(mote.s) * delta, 1.04)
	for walker in walkers:
		walker.phase = fposmod(float(walker.phase) + float(walker.speed) * delta, 1.0)
	queue_redraw()

func _draw() -> void:
	var s := size
	if s.x <= 0.0 or s.y <= 0.0:
		return
	_draw_moon(s)
	_draw_clouds(s)
	_draw_lanterns(s)
	_draw_walkers(s)
	_draw_mist(s)
	_draw_motes(s)

func _draw_moon(s: Vector2) -> void:
	var motion := 0.0 if reduce_motion else elapsed
	var pos := Vector2(
		s.x * (0.57 + sin(motion * 0.018) * 0.055),
		s.y * (0.135 + cos(motion * 0.014) * 0.018)
	)
	var radius := clampf(minf(s.x, s.y) * 0.045, 24.0, 58.0)
	for i in range(6, 0, -1):
		var halo_radius := radius * (1.0 + float(i) * 0.34)
		draw_circle(pos, halo_radius, Color(0.78, 0.86, 0.93, 0.008 + float(6 - i) * 0.008))
	draw_circle(pos, radius, Color(0.88, 0.91, 0.88, 0.82))
	draw_circle(pos + Vector2(-radius * 0.24, radius * 0.12), radius * 0.23, Color(0.58, 0.64, 0.66, 0.16))
	draw_circle(pos + Vector2(radius * 0.28, -radius * 0.18), radius * 0.13, Color(0.58, 0.64, 0.66, 0.13))

func _draw_clouds(s: Vector2) -> void:
	var motion := 0.0 if reduce_motion else elapsed
	_draw_cloud_band(s, s.y * 0.105, motion * 4.2, 0.036, 1.0)
	_draw_cloud_band(s, s.y * 0.205, motion * 2.6 + s.x * 0.31, 0.024, 1.28)
	_draw_cloud_band(s, s.y * 0.31, motion * 1.5 + s.x * 0.68, 0.014, 1.65)

func _draw_cloud_band(s: Vector2, y: float, offset: float, alpha: float, cloud_scale: float) -> void:
	var band_width := s.x * 1.05
	var start := fposmod(offset, band_width) - band_width
	var thickness := clampf(s.y * 0.055 * cloud_scale, 30.0, 100.0)
	for repeat in 3:
		var origin := start + float(repeat) * band_width
		var points := PackedVector2Array()
		for j in 16:
			var t := float(j) / 15.0
			var wave := sin(t * TAU * 2.0 + cloud_scale) * thickness * 0.16 + sin(t * TAU * 5.0) * thickness * 0.06
			points.append(Vector2(origin + t * band_width, y + wave - thickness * (0.38 + sin(t * TAU * 3.0) * 0.08)))
		for j in range(15, -1, -1):
			var t := float(j) / 15.0
			var wave := sin(t * TAU * 2.0 + cloud_scale) * thickness * 0.16 + sin(t * TAU * 5.0) * thickness * 0.06
			points.append(Vector2(origin + t * band_width, y + wave + thickness * (0.38 + cos(t * TAU * 2.0) * 0.08)))
		draw_colored_polygon(points, Color(0.56, 0.63, 0.70, alpha))

func _draw_lanterns(s: Vector2) -> void:
	for i in LANTERNS.size():
		var pulse := 0.78 if reduce_motion else 0.76 + sin(elapsed * (2.2 + float(i) * 0.11) + float(i) * 1.7) * 0.18
		var pos: Vector2 = LANTERNS[i] * s
		var radius := clampf(s.x * 0.0065, 4.0, 11.0)
		for ring in range(8, 0, -1):
			var ring_t := float(9 - ring) / 8.0
			draw_circle(pos, radius * (1.0 + float(ring) * 0.42), Color(1.0, 0.35 + ring_t * 0.18, 0.14, (0.005 + ring_t * 0.014) * pulse))
		draw_circle(pos, radius * 0.72, Color(1.0, 0.68, 0.34, 0.30 * pulse))

func _draw_walkers(s: Vector2) -> void:
	for i in walkers.size():
		var walker := walkers[i]
		var t := float(walker.phase)
		var depth := pow(t, 1.42)
		var lane := float(walker.lane)
		var gait := sin(elapsed * 4.0 + float(i) * 1.9)
		var foot := Vector2(
			s.x * (0.5 + lane * depth * 0.23 + gait * depth * 0.003),
			lerpf(s.y * 0.555, s.y * 1.03, depth)
		)
		var height := lerpf(s.y * 0.022, s.y * 0.125, depth)
		var width := height * 0.27
		var body_color: Color = walker.color
		body_color.a = 0.78
		var rim := Color(0.72, 0.48, 0.31, 0.16 + depth * 0.10)
		var head := foot - Vector2(0.0, height * 0.82)
		draw_circle(head, width * 0.42, Color("#171a20"))
		draw_colored_polygon(PackedVector2Array([
			head + Vector2(-width * 0.40, width * 0.34),
			head + Vector2(width * 0.40, width * 0.34),
			foot + Vector2(width * 0.72, -height * 0.10),
			foot + Vector2(-width * 0.72, -height * 0.10)
		]), body_color)
		var hip := foot - Vector2(0.0, height * 0.28)
		var stride := width * 0.42 * gait
		draw_line(hip, foot + Vector2(stride, 0.0), Color("#151820"), maxf(1.0, width * 0.21), true)
		draw_line(hip, foot - Vector2(stride, 0.0), Color("#151820"), maxf(1.0, width * 0.21), true)
		var shoulder := head + Vector2(0.0, height * 0.23)
		draw_line(shoulder, shoulder + Vector2(-width * 0.95, height * 0.24 + stride), body_color.lightened(0.04), maxf(1.0, width * 0.18), true)
		draw_line(shoulder, shoulder + Vector2(width * 0.95, height * 0.24 - stride), body_color.lightened(0.04), maxf(1.0, width * 0.18), true)
		draw_line(head + Vector2(width * 0.35, 0.0), foot + Vector2(width * 0.58, -height * 0.11), rim, maxf(1.0, width * 0.08), true)

func _draw_mist(s: Vector2) -> void:
	var motion := 0.0 if reduce_motion else elapsed
	for i in 5:
		var y := s.y * (0.50 + float(i) * 0.105)
		var drift := sin(motion * (0.08 + float(i) * 0.012) + float(i)) * s.x * 0.04
		var points := PackedVector2Array()
		for j in 9:
			var x := -s.x * 0.12 + float(j) * s.x * 0.16
			points.append(Vector2(x + drift, y + sin(float(j) * 1.3 + motion * 0.09) * s.y * 0.012))
		draw_polyline(points, Color(0.72, 0.78, 0.82, 0.028 + float(i) * 0.006), s.y * (0.020 + float(i) * 0.004), true)

func _draw_motes(s: Vector2) -> void:
	for mote in motes:
		var pulse := 0.72 if reduce_motion else 0.54 + sin(elapsed * 1.2 + float(mote.p)) * 0.18
		var pos := Vector2(float(mote.x) * s.x, float(mote.y) * s.y)
		draw_circle(pos, float(mote.r), Color(1.0, 0.54, 0.24, pulse))
