extends Control

signal finished(score: float)
signal round_started(round_number: int, total_rounds: int)
signal struck(score: float, perfect: bool)

var active := false
var value := 0.0
var direction := 1.0
var round_index := 0
var round_count := 3
var total_score := 0.0
var target_center := 0.54
var target_width := 0.18
var speed := 0.82

func _ready() -> void:
	custom_minimum_size = Vector2(280, 100)
	mouse_filter = Control.MOUSE_FILTER_STOP
	set_process(false)

func start(rounds: int = 3) -> void:
	round_count = rounds
	round_index = 0
	total_score = 0.0
	value = 0.08
	direction = 1.0
	active = true
	set_process(true)
	queue_redraw()
	round_started.emit(1, round_count)

func _process(delta: float) -> void:
	if not active:
		return
	value += direction * speed * delta
	if value >= 1.0:
		value = 1.0
		direction = -1.0
	elif value <= 0.0:
		value = 0.0
		direction = 1.0
	queue_redraw()

func _gui_input(event: InputEvent) -> void:
	if not active:
		return
	if event is InputEventMouseButton and event.pressed:
		_strike()
	elif event is InputEventScreenTouch and event.pressed:
		_strike()

func _unhandled_key_input(event: InputEvent) -> void:
	if active and event.is_action_pressed("ui_accept"):
		_strike()

func _strike() -> void:
	var distance := absf(value - target_center)
	var round_score := clampf(1.0 - distance / 0.5, 0.0, 1.0)
	var perfect := distance <= target_width * 0.5
	if perfect:
		round_score = 1.0
	struck.emit(round_score, perfect)
	total_score += round_score
	round_index += 1
	if round_index >= round_count:
		active = false
		set_process(false)
		queue_redraw()
		finished.emit(total_score / float(round_count))
		return
	target_center = [0.68, 0.39, 0.57][round_index % 3]
	target_width = maxf(0.11, target_width - 0.025)
	speed += 0.16
	value = 0.06
	direction = 1.0
	queue_redraw()
	round_started.emit(round_index + 1, round_count)

func _draw() -> void:
	var font := get_theme_default_font()
	var line_y := size.y * 0.58
	var left := 12.0
	var width := size.x - 24.0
	draw_string(font, Vector2(left, 22), "修爐火候  %d / %d" % [mini(round_index + 1, round_count), round_count], HORIZONTAL_ALIGNMENT_LEFT, -1, 17, Color("#e0d2b0"))
	draw_rect(Rect2(left, line_y - 5, width, 10), Color(0.12, 0.13, 0.15, 0.96), true)
	var target_x := left + width * (target_center - target_width * 0.5)
	draw_rect(Rect2(target_x, line_y - 8, width * target_width, 16), Color("#8f6c35"), true)
	draw_line(Vector2(left, line_y), Vector2(left + width, line_y), Color("#70695e"), 2.0)
	var needle_x := left + width * value
	draw_line(Vector2(needle_x, line_y - 20), Vector2(needle_x, line_y + 20), Color("#f0c56e"), 4.0)
	draw_circle(Vector2(needle_x, line_y), 6.0, Color("#c44232"))
	var hint := "點擊或按空白鍵 · 停在金色區" if size.x < 320 else "點擊火候尺或按空白鍵，令指針停在金色區域。"
	draw_string(font, Vector2(left, size.y - 6), hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color("#bcc2c9"))
