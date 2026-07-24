extends Control

const BG := Color("#090b0e")
const SURFACE := Color("#12161c")
const SURFACE_SOFT := Color("#171c23")
const TEXT := Color("#f0eee9")
const MUTED := Color("#9ca2aa")
const LINE := Color("#343a43")
const ACCENT := Color("#b8453b")
const ACCENT_HOVER := Color("#cd5045")
const ERROR := Color("#ef8d84")

var reduce_motion := false
var atmosphere: WuxiaAtmosphere
var brand: VBoxContainer
var panel: PanelContainer
var form_margin: MarginContainer
var form_root: VBoxContainer
var form_copy_label: Label
var preview_note: Label
var success_content: VBoxContainer
var account: LineEdit
var secret: LineEdit
var error_label: Label
var success_layer: ColorRect
var success_title: Label
var success_copy: Label
var enter_button: Button
var guest_button: Button

func _ready() -> void:
	reduce_motion = _prefers_reduced_motion()
	_build_scene()
	_apply_layout()
	get_viewport().size_changed.connect(_apply_layout)
	if not reduce_motion:
		_play_intro()

func _build_scene() -> void:
	var app_theme := Theme.new()
	var app_font: Font = load("res://assets/fonts/NotoSansTC-Variable.ttf")
	app_theme.default_font = app_font
	app_theme.default_font_size = 15
	theme = app_theme

	var backdrop := TextureRect.new()
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.texture = load("res://assets/bg/town.jpg")
	backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	backdrop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	backdrop.modulate = Color(0.50, 0.54, 0.59, 0.58)
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(backdrop)

	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.025, 0.031, 0.040, 0.62)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)

	atmosphere = WuxiaAtmosphere.new()
	atmosphere.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	atmosphere.reduce_motion = reduce_motion
	atmosphere.modulate = Color(1, 1, 1, 0.34)
	add_child(atmosphere)

	brand = VBoxContainer.new()
	brand.add_theme_constant_override("separation", 14)
	add_child(brand)

	var seal := Label.new()
	seal.text = "俠"
	seal.custom_minimum_size = Vector2(54, 54)
	seal.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	seal.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	seal.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	seal.add_theme_font_size_override("font_size", 25)
	seal.add_theme_color_override("font_color", TEXT)
	seal.add_theme_stylebox_override("normal", _box(ACCENT, ACCENT, 8, 0))
	brand.add_child(seal)

	var title := Label.new()
	title.text = "俠 客 行"
	title.add_theme_font_size_override("font_size", 58)
	title.add_theme_color_override("font_color", TEXT)
	brand.add_child(title)

	var rule := HSeparator.new()
	rule.custom_minimum_size = Vector2(88, 1)
	rule.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	rule.add_theme_stylebox_override("separator", _box(ACCENT, ACCENT, 0, 0))
	brand.add_child(rule)

	var statement := Label.new()
	statement.text = "今夜，江湖有門。"
	statement.add_theme_font_size_override("font_size", 28)
	statement.add_theme_color_override("font_color", TEXT)
	brand.add_child(statement)

	var subcopy := Label.new()
	subcopy.text = "沿青石路入鎮，續寫你的名號。"
	subcopy.add_theme_font_size_override("font_size", 16)
	subcopy.add_theme_color_override("font_color", MUTED)
	brand.add_child(subcopy)

	panel = PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _box(SURFACE, LINE, 14, 1))
	add_child(panel)

	form_margin = MarginContainer.new()
	form_margin.add_theme_constant_override("margin_left", 34)
	form_margin.add_theme_constant_override("margin_top", 30)
	form_margin.add_theme_constant_override("margin_right", 34)
	form_margin.add_theme_constant_override("margin_bottom", 28)
	panel.add_child(form_margin)

	form_root = VBoxContainer.new()
	form_root.add_theme_constant_override("separation", 12)
	form_margin.add_child(form_root)

	var form_title := Label.new()
	form_title.text = "回到青石鎮"
	form_title.add_theme_font_size_override("font_size", 25)
	form_title.add_theme_color_override("font_color", TEXT)
	form_root.add_child(form_title)

	form_copy_label = Label.new()
	form_copy_label.text = "輸入名號，繼續你的江湖路。"
	form_copy_label.add_theme_font_size_override("font_size", 14)
	form_copy_label.add_theme_color_override("font_color", MUTED)
	form_root.add_child(form_copy_label)

	form_root.add_child(_spacer(8))
	form_root.add_child(_field_label("帳號"))
	account = _line_edit("少俠名號")
	account.text_submitted.connect(func(_value: String) -> void: secret.grab_focus())
	form_root.add_child(account)

	form_root.add_child(_field_label("密語"))
	secret = _line_edit("江湖密語")
	secret.secret = true
	secret.text_submitted.connect(func(_value: String) -> void: _submit())
	form_root.add_child(secret)

	error_label = Label.new()
	error_label.text = " "
	error_label.custom_minimum_size.y = 24
	error_label.add_theme_font_size_override("font_size", 13)
	error_label.add_theme_color_override("font_color", ERROR)
	form_root.add_child(error_label)

	enter_button = _button("進入江湖", true)
	enter_button.pressed.connect(_submit)
	form_root.add_child(enter_button)

	guest_button = _button("遊客試玩", false)
	guest_button.pressed.connect(func() -> void: _complete("遊客", true))
	form_root.add_child(guest_button)

	var links := HBoxContainer.new()
	links.alignment = BoxContainer.ALIGNMENT_CENTER
	links.add_theme_constant_override("separation", 18)
	form_root.add_child(links)

	var demo := LinkButton.new()
	demo.text = "填入示範"
	demo.add_theme_font_size_override("font_size", 13)
	demo.add_theme_color_override("font_color", MUTED)
	demo.pressed.connect(_fill_demo)
	links.add_child(demo)

	var clear := LinkButton.new()
	clear.text = "清除"
	clear.add_theme_font_size_override("font_size", 13)
	clear.add_theme_color_override("font_color", MUTED)
	clear.pressed.connect(_clear_form)
	links.add_child(clear)

	preview_note = Label.new()
	preview_note.text = "此為登入門面預覽，帳號系統尚未接入。"
	preview_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	preview_note.add_theme_font_size_override("font_size", 12)
	preview_note.add_theme_color_override("font_color", Color(0.49, 0.52, 0.57, 1))
	form_root.add_child(preview_note)

	_build_success_layer()
	account.grab_focus()

func _build_success_layer() -> void:
	success_layer = ColorRect.new()
	success_layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	success_layer.color = Color(0.025, 0.031, 0.040, 0.97)
	success_layer.visible = false
	success_layer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(success_layer)

	success_content = VBoxContainer.new()
	success_content.set_anchors_preset(Control.PRESET_TOP_LEFT)
	success_content.position = Vector2.ZERO
	success_content.size = Vector2(380, 240)
	success_content.alignment = BoxContainer.ALIGNMENT_CENTER
	success_content.add_theme_constant_override("separation", 18)
	success_layer.add_child(success_content)

	var seal := Label.new()
	seal.text = "入"
	seal.custom_minimum_size = Vector2(52, 52)
	seal.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	seal.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	seal.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	seal.add_theme_font_size_override("font_size", 23)
	seal.add_theme_stylebox_override("normal", _box(ACCENT, ACCENT, 8, 0))
	success_content.add_child(seal)

	success_title = Label.new()
	success_title.text = "門扉已開"
	success_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	success_title.add_theme_font_size_override("font_size", 28)
	success_title.add_theme_color_override("font_color", TEXT)
	success_content.add_child(success_title)

	success_copy = Label.new()
	success_copy.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	success_copy.add_theme_font_size_override("font_size", 15)
	success_copy.add_theme_color_override("font_color", MUTED)
	success_content.add_child(success_copy)

	var actions := HBoxContainer.new()
	actions.alignment = BoxContainer.ALIGNMENT_CENTER
	actions.add_theme_constant_override("separation", 10)
	success_content.add_child(actions)

	var continue_button := _button("前往遊戲", true)
	continue_button.custom_minimum_size.x = 150
	continue_button.pressed.connect(_go_to_game)
	actions.add_child(continue_button)

	var back_button := _button("返回", false)
	back_button.custom_minimum_size.x = 110
	back_button.pressed.connect(_close_success)
	actions.add_child(back_button)

func _apply_layout() -> void:
	var s := get_viewport_rect().size
	var mobile := s.x < 760.0
	if mobile:
		var pad := clampf(s.x * 0.055, 18.0, 28.0)
		var compact := s.y < 720.0
		brand.position = Vector2(pad, 24)
		brand.size = Vector2(s.x - pad * 2.0, 154)
		brand.get_child(0).visible = not compact
		brand.get_child(1).add_theme_font_size_override("font_size", 36 if compact else 38)
		brand.get_child(2).visible = not compact
		brand.get_child(3).visible = false
		brand.get_child(4).visible = false
		form_root.add_theme_constant_override("separation", 8 if compact else 10)
		form_margin.add_theme_constant_override("margin_top", 20 if compact else 24)
		form_margin.add_theme_constant_override("margin_bottom", 18 if compact else 22)
		form_margin.add_theme_constant_override("margin_left", 22)
		form_margin.add_theme_constant_override("margin_right", 22)
		form_copy_label.visible = not compact
		preview_note.visible = not compact
		var panel_top := 142.0 if compact else 170.0
		panel.position = Vector2(pad, panel_top)
		panel.size = Vector2(s.x - pad * 2.0, s.y - panel_top - 18.0)
	else:
		var panel_width := clampf(s.x * 0.30, 390.0, 450.0)
		brand.get_child(0).visible = true
		brand.position = Vector2(s.x * 0.075, s.y * 0.28)
		brand.size = Vector2(s.x * 0.44, 340)
		brand.get_child(1).add_theme_font_size_override("font_size", 58)
		brand.get_child(2).visible = true
		brand.get_child(3).add_theme_font_size_override("font_size", 28)
		brand.get_child(3).visible = true
		brand.get_child(4).visible = true
		form_root.add_theme_constant_override("separation", 12)
		form_margin.add_theme_constant_override("margin_left", 34)
		form_margin.add_theme_constant_override("margin_top", 30)
		form_margin.add_theme_constant_override("margin_right", 34)
		form_margin.add_theme_constant_override("margin_bottom", 28)
		form_copy_label.visible = true
		preview_note.visible = true
		panel.position = Vector2(s.x - panel_width - s.x * 0.075, (s.y - 550.0) * 0.5)
		panel.size = Vector2(panel_width, 550)
	var success_width := minf(380.0, s.x - 36.0)
	success_content.position = Vector2((s.x - success_width) * 0.5, (s.y - 240.0) * 0.5)
	success_content.size = Vector2(success_width, 240)

func _play_intro() -> void:
	brand.modulate.a = 0.0
	brand.position.y += 18.0
	panel.modulate.a = 0.0
	panel.position.x += 24.0
	var brand_target := brand.position - Vector2(0, 18)
	var panel_target := panel.position - Vector2(24, 0)
	var tween := create_tween().set_parallel(true)
	tween.set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	tween.tween_property(brand, "modulate:a", 1.0, 0.72)
	tween.tween_property(brand, "position", brand_target, 0.72)
	tween.tween_property(panel, "modulate:a", 1.0, 0.72).set_delay(0.10)
	tween.tween_property(panel, "position", panel_target, 0.72).set_delay(0.10)

func _submit() -> void:
	var name := account.text.strip_edges()
	if name.is_empty():
		_show_error("請留下少俠名號")
		account.grab_focus()
		return
	if secret.text.is_empty():
		_show_error("請輸入江湖密語")
		secret.grab_focus()
		return
	_complete(name, false)

func _show_error(message: String) -> void:
	error_label.text = message
	if reduce_motion:
		return
	var origin := panel.position
	var tween := create_tween()
	for offset in [-7.0, 7.0, -4.0, 4.0, 0.0]:
		tween.tween_property(panel, "position:x", origin.x + offset, 0.045)

func _fill_demo() -> void:
	account.text = "青石少年"
	secret.text = "江湖"
	error_label.text = " "
	secret.grab_focus()

func _clear_form() -> void:
	account.clear()
	secret.clear()
	error_label.text = " "
	account.grab_focus()

func _complete(name: String, guest: bool) -> void:
	error_label.text = " "
	success_copy.text = "遊客模式已準備好。" if guest else "少俠「%s」，你的旅程已準備好。" % name
	success_layer.visible = true
	success_layer.modulate.a = 1.0 if reduce_motion else 0.0
	if not reduce_motion:
		create_tween().tween_property(success_layer, "modulate:a", 1.0, 0.36)

func _close_success() -> void:
	if reduce_motion:
		success_layer.visible = false
		return
	var tween := create_tween()
	tween.tween_property(success_layer, "modulate:a", 0.0, 0.24)
	tween.tween_callback(func() -> void: success_layer.visible = false)

func _go_to_game() -> void:
	if OS.has_feature("web"):
		JavaScriptBridge.eval("window.location.href='../wuxia-game.html';")
	else:
		success_copy.text = "網頁匯出後，此按鈕會開啟現有遊戲。"

func _prefers_reduced_motion() -> bool:
	if not OS.has_feature("web"):
		return false
	var value: Variant = JavaScriptBridge.eval("window.matchMedia('(prefers-reduced-motion: reduce)').matches")
	return bool(value)

func _field_label(value: String) -> Label:
	var label := Label.new()
	label.text = value
	label.add_theme_font_size_override("font_size", 13)
	label.add_theme_color_override("font_color", TEXT)
	return label

func _line_edit(placeholder: String) -> LineEdit:
	var edit := LineEdit.new()
	edit.placeholder_text = placeholder
	edit.custom_minimum_size = Vector2(0, 48)
	edit.add_theme_font_size_override("font_size", 16)
	edit.add_theme_color_override("font_color", TEXT)
	edit.add_theme_color_override("font_placeholder_color", Color(0.50, 0.53, 0.58, 1))
	edit.add_theme_color_override("caret_color", ACCENT)
	edit.add_theme_stylebox_override("normal", _box(Color("#0d1116"), LINE, 12, 1))
	edit.add_theme_stylebox_override("focus", _box(Color("#0d1116"), ACCENT, 12, 2))
	return edit

func _button(label: String, primary: bool) -> Button:
	var button := Button.new()
	button.text = label
	button.custom_minimum_size = Vector2(0, 48)
	button.add_theme_font_size_override("font_size", 15)
	button.add_theme_color_override("font_color", TEXT)
	button.add_theme_color_override("font_hover_color", TEXT)
	button.add_theme_color_override("font_pressed_color", TEXT)
	if primary:
		button.add_theme_stylebox_override("normal", _box(ACCENT, ACCENT, 12, 0))
		button.add_theme_stylebox_override("hover", _box(ACCENT_HOVER, ACCENT_HOVER, 12, 0))
		button.add_theme_stylebox_override("pressed", _box(Color("#9f3932"), Color("#9f3932"), 12, 0))
	else:
		button.add_theme_stylebox_override("normal", _box(SURFACE_SOFT, LINE, 12, 1))
		button.add_theme_stylebox_override("hover", _box(Color("#202630"), Color("#59616d"), 12, 1))
		button.add_theme_stylebox_override("pressed", _box(Color("#0f1319"), LINE, 12, 1))
	return button

func _box(fill: Color, border: Color, radius: int, border_width: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(border_width)
	style.set_corner_radius_all(radius)
	style.content_margin_left = 13
	style.content_margin_right = 13
	style.content_margin_top = 9
	style.content_margin_bottom = 9
	return style

func _spacer(height: float) -> Control:
	var spacer := Control.new()
	spacer.custom_minimum_size.y = height
	return spacer
