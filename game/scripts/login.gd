extends Control

const OST_SCRIPT = preload("res://scripts/wuxia_ost.gd")
const TOWN_3D_SCRIPT = preload("res://scripts/town_3d.gd")
const TOWN_BACKDROP = preload("res://assets/bg/town-hybrid.jpg")
const BG := Color("#090b0e")
const SURFACE := Color("#12161c")
const SURFACE_SOFT := Color("#171c23")
const TEXT := Color("#f0eee9")
const MUTED := Color("#9ca2aa")
const LINE := Color("#343a43")
const ACCENT := Color("#b8453b")
const ACCENT_HOVER := Color("#cd5045")
const GOLD := Color("#d8b86e")
const ERROR := Color("#ef8d84")

var reduce_motion := false
var town_backdrop: TextureRect
var town_3d: SubViewportContainer
var brand: VBoxContainer
var title_stage: Control
var title_art: Node2D
var title_ink_wash: Polygon2D
var title_brush: Line2D
var title_brush_tip: Line2D
var title_echo_top: Label
var title_echo_bottom: Label
var title_top: Label
var title_bottom: Label
var title_kicker: Label
var title_seal: Label
var brand_statement: Label
var brand_subcopy: Label
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
var music_button: Button
var demo_link: LinkButton
var clear_link: LinkButton
var success_continue_button: Button
var success_back_button: Button
var ost: WuxiaOST
var session_player_name := "無名"
var login_transitioning := false

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

	town_backdrop = TextureRect.new()
	town_backdrop.name = "PaintedTownBackdrop"
	town_backdrop.texture = TOWN_BACKDROP
	town_backdrop.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	town_backdrop.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	town_backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	town_backdrop.offset_left = -34.0
	town_backdrop.offset_top = -18.0
	town_backdrop.offset_right = 34.0
	town_backdrop.offset_bottom = 18.0
	town_backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(town_backdrop)

	town_3d = TOWN_3D_SCRIPT.new()
	town_3d.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	town_3d.reduce_motion = reduce_motion
	town_3d.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(town_3d)

	var shade := ColorRect.new()
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.color = Color(0.025, 0.031, 0.040, 0.06)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)

	ost = OST_SCRIPT.new()
	add_child(ost)

	music_button = _button("音樂 · 關" if ost.is_music_paused() else "音樂 · 開", false)
	music_button.custom_minimum_size = Vector2(104, 36)
	music_button.add_theme_font_size_override("font_size", 12)
	music_button.tooltip_text = "開啟或關閉古箏主題配樂"
	music_button.pressed.connect(_toggle_music)
	add_child(music_button)

	brand = VBoxContainer.new()
	brand.add_theme_constant_override("separation", 10)
	add_child(brand)

	_build_artistic_title()

	var rule := HSeparator.new()
	rule.custom_minimum_size = Vector2(228, 1)
	rule.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	var rule_style := StyleBoxFlat.new()
	rule_style.bg_color = Color(GOLD, 0.64)
	rule.add_theme_stylebox_override("separator", rule_style)
	brand.add_child(rule)

	brand_statement = Label.new()
	brand_statement.text = "一餅起家  ·  十日改命"
	brand_statement.add_theme_font_override("font", load("res://assets/fonts/NotoSerifTC-Variable.ttf"))
	brand_statement.add_theme_font_size_override("font_size", 24)
	brand_statement.add_theme_color_override("font_color", Color("#f1e5c8"))
	brand.add_child(brand_statement)

	brand_subcopy = Label.new()
	brand_subcopy.text = "穿越陽谷縣，重寫武大郎的命數。"
	brand_subcopy.add_theme_font_size_override("font_size", 15)
	brand_subcopy.add_theme_color_override("font_color", Color("#b7afa2"))
	brand.add_child(brand_subcopy)

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
	form_title.text = "重返陽谷縣"
	form_title.add_theme_font_size_override("font_size", 25)
	form_title.add_theme_color_override("font_color", TEXT)
	form_root.add_child(form_title)

	form_copy_label = Label.new()
	form_copy_label.text = "輸入名號，繼續你的逆命之路。"
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
	demo_link = demo
	links.add_child(demo)

	var clear := LinkButton.new()
	clear.text = "清除"
	clear.add_theme_font_size_override("font_size", 13)
	clear.add_theme_color_override("font_color", MUTED)
	clear.pressed.connect(_clear_form)
	clear_link = clear
	links.add_child(clear)

	preview_note = Label.new()
	preview_note.text = "此為登入門面預覽，帳號系統尚未接入。"
	preview_note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	preview_note.add_theme_font_size_override("font_size", 12)
	preview_note.add_theme_color_override("font_color", Color(0.49, 0.52, 0.57, 1))
	form_root.add_child(preview_note)

	_build_success_layer()
	account.grab_focus()

func _build_artistic_title() -> void:
	var serif_font: Font = load("res://assets/fonts/NotoSerifTC-Variable.ttf")
	title_stage = Control.new()
	title_stage.name = "ArtisticGameTitle"
	title_stage.custom_minimum_size = Vector2(470, 206)
	title_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	brand.add_child(title_stage)

	title_art = Node2D.new()
	title_stage.add_child(title_art)

	title_ink_wash = Polygon2D.new()
	title_ink_wash.polygon = PackedVector2Array([
		Vector2(-22, 60),
		Vector2(286, 31),
		Vector2(438, 62),
		Vector2(401, 113),
		Vector2(92, 145),
		Vector2(-36, 112)
	])
	title_ink_wash.color = Color(0.075, 0.045, 0.036, 0.58)
	title_art.add_child(title_ink_wash)

	title_brush = Line2D.new()
	title_brush.points = PackedVector2Array([
		Vector2(-16, 160),
		Vector2(76, 150),
		Vector2(202, 163),
		Vector2(326, 147),
		Vector2(431, 123)
	])
	title_brush.width = 7.0
	title_brush.default_color = Color(0.76, 0.56, 0.25, 0.46)
	title_brush.antialiased = true
	title_art.add_child(title_brush)

	title_brush_tip = Line2D.new()
	title_brush_tip.points = PackedVector2Array([
		Vector2(360, 151),
		Vector2(438, 123),
		Vector2(461, 101)
	])
	title_brush_tip.width = 2.0
	title_brush_tip.default_color = Color(0.95, 0.82, 0.48, 0.74)
	title_brush_tip.antialiased = true
	title_art.add_child(title_brush_tip)

	title_echo_top = _title_label("逆命", serif_font, Color(0.19, 0.035, 0.028, 0.92))
	title_stage.add_child(title_echo_top)
	title_echo_bottom = _title_label("大郎", serif_font, Color(0.19, 0.035, 0.028, 0.92))
	title_stage.add_child(title_echo_bottom)

	title_top = _title_label("逆命", serif_font, Color.WHITE)
	title_top.material = _title_gradient_material()
	title_stage.add_child(title_top)
	title_bottom = _title_label("大郎", serif_font, Color.WHITE)
	title_bottom.material = _title_gradient_material()
	title_stage.add_child(title_bottom)

	title_kicker = Label.new()
	title_kicker.text = "大宋 · 陽谷縣\n凡人改命錄"
	title_kicker.add_theme_font_override("font", serif_font)
	title_kicker.add_theme_font_size_override("font_size", 14)
	title_kicker.add_theme_color_override("font_color", Color("#d6bd82"))
	title_kicker.add_theme_constant_override("line_spacing", 7)
	title_stage.add_child(title_kicker)

	title_seal = Label.new()
	title_seal.text = "武\n記"
	title_seal.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title_seal.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	title_seal.add_theme_font_override("font", serif_font)
	title_seal.add_theme_font_size_override("font_size", 19)
	title_seal.add_theme_color_override("font_color", Color("#f5dcc5"))
	title_seal.add_theme_stylebox_override("normal", _seal_style())
	title_stage.add_child(title_seal)

	_apply_title_layout(false, false)

func _title_label(value: String, font: Font, color: Color) -> Label:
	var label := Label.new()
	label.text = value
	label.add_theme_font_override("font", font)
	label.add_theme_color_override("font_color", color)
	label.add_theme_color_override("font_outline_color", Color(0.055, 0.025, 0.018, 0.96))
	label.add_theme_constant_override("outline_size", 5)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label

func _seal_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("#9f302b")
	style.border_color = Color("#e1aa7b")
	style.set_border_width_all(2)
	style.set_corner_radius_all(3)
	style.content_margin_left = 8
	style.content_margin_right = 8
	style.content_margin_top = 5
	style.content_margin_bottom = 5
	return style

func _apply_title_layout(mobile: bool, compact: bool) -> void:
	if mobile:
		var viewport_width := get_viewport_rect().size.x
		var horizontal_pad := clampf(viewport_width * 0.055, 18.0, 28.0)
		var available_width := viewport_width - horizontal_pad * 2.0
		var mobile_title_size := 43 if viewport_width < 360.0 else (48 if compact else 52)
		title_stage.custom_minimum_size = Vector2(0, 76 if compact else 88)
		title_top.text = "逆命大郎"
		title_echo_top.text = "逆命大郎"
		title_top.position = Vector2(0, -8)
		title_echo_top.position = Vector2(4, -4)
		title_top.size = Vector2(available_width, 76)
		title_echo_top.size = title_top.size
		title_top.add_theme_font_size_override("font_size", mobile_title_size)
		title_echo_top.add_theme_font_size_override("font_size", mobile_title_size)
		title_bottom.visible = false
		title_echo_bottom.visible = false
		title_kicker.visible = false
		title_seal.position = Vector2(available_width - 42, 31 if compact else 38)
		title_seal.size = Vector2(38, 42)
		title_seal.add_theme_font_size_override("font_size", 14)
		title_art.scale = Vector2(0.72, 0.43)
		title_art.position = Vector2(2, -6)
	else:
		title_stage.custom_minimum_size = Vector2(470, 206)
		title_top.text = "逆命"
		title_echo_top.text = "逆命"
		title_bottom.text = "大郎"
		title_echo_bottom.text = "大郎"
		title_top.position = Vector2(0, -17)
		title_echo_top.position = Vector2(6, -11)
		title_bottom.position = Vector2(76, 70)
		title_echo_bottom.position = Vector2(82, 76)
		title_top.size = Vector2(292, 124)
		title_echo_top.size = title_top.size
		title_bottom.size = Vector2(300, 132)
		title_echo_bottom.size = title_bottom.size
		title_top.add_theme_font_size_override("font_size", 94)
		title_echo_top.add_theme_font_size_override("font_size", 94)
		title_bottom.add_theme_font_size_override("font_size", 102)
		title_echo_bottom.add_theme_font_size_override("font_size", 102)
		title_bottom.visible = true
		title_echo_bottom.visible = true
		title_kicker.visible = true
		title_kicker.position = Vector2(346, 33)
		title_kicker.size = Vector2(120, 72)
		title_seal.position = Vector2(356, 116)
		title_seal.size = Vector2(48, 58)
		title_seal.add_theme_font_size_override("font_size", 19)
		title_art.scale = Vector2.ONE
		title_art.position = Vector2.ZERO

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
	success_continue_button = continue_button
	actions.add_child(continue_button)

	var back_button := _button("返回", false)
	back_button.custom_minimum_size.x = 110
	back_button.pressed.connect(_close_success)
	success_back_button = back_button
	actions.add_child(back_button)

func _apply_layout() -> void:
	var s := get_viewport_rect().size
	var mobile := s.x < 760.0
	music_button.position = Vector2(s.x - 124.0, 18.0)
	music_button.size = Vector2(104.0, 36.0)
	if mobile:
		var pad := clampf(s.x * 0.055, 18.0, 28.0)
		var compact := s.y < 720.0
		brand.position = Vector2(pad, 54)
		brand.size = Vector2(s.x - pad * 2.0, 126 if compact else 152)
		brand.add_theme_constant_override("separation", 8)
		_apply_title_layout(true, compact)
		brand.get_child(1).visible = not compact
		brand_statement.visible = not compact
		brand_statement.add_theme_font_size_override("font_size", 17)
		brand_subcopy.visible = false
		form_root.add_theme_constant_override("separation", 10 if compact else 12)
		form_margin.add_theme_constant_override("margin_top", 20 if compact else 24)
		form_margin.add_theme_constant_override("margin_bottom", 18 if compact else 22)
		form_margin.add_theme_constant_override("margin_left", 22)
		form_margin.add_theme_constant_override("margin_right", 22)
		form_copy_label.visible = not compact
		form_copy_label.add_theme_font_size_override("font_size", 15)
		preview_note.visible = not compact
		preview_note.add_theme_font_size_override("font_size", 14)
		account.add_theme_font_size_override("font_size", 18)
		secret.add_theme_font_size_override("font_size", 18)
		error_label.add_theme_font_size_override("font_size", 15)
		enter_button.add_theme_font_size_override("font_size", 17)
		guest_button.add_theme_font_size_override("font_size", 17)
		if demo_link != null:
			demo_link.add_theme_font_size_override("font_size", 15)
		if clear_link != null:
			clear_link.add_theme_font_size_override("font_size", 15)
		music_button.add_theme_font_size_override("font_size", 14)
		if success_continue_button != null:
			success_continue_button.add_theme_font_size_override("font_size", 16)
		if success_back_button != null:
			success_back_button.add_theme_font_size_override("font_size", 16)
		success_title.add_theme_font_size_override("font_size", 26)
		success_copy.add_theme_font_size_override("font_size", 16)
		var panel_top := 148.0 if compact else 194.0
		panel.position = Vector2(pad, panel_top)
		panel.size = Vector2(s.x - pad * 2.0, s.y - panel_top - 18.0)
	else:
		var panel_width := clampf(s.x * 0.30, 390.0, 450.0)
		brand.position = Vector2(s.x * 0.068, s.y * 0.205)
		brand.size = Vector2(s.x * 0.44, 350)
		brand.add_theme_constant_override("separation", 10)
		_apply_title_layout(false, false)
		brand.get_child(1).visible = true
		brand_statement.add_theme_font_size_override("font_size", 24)
		brand_statement.visible = true
		brand_subcopy.visible = true
		form_root.add_theme_constant_override("separation", 12)
		form_margin.add_theme_constant_override("margin_left", 34)
		form_margin.add_theme_constant_override("margin_top", 30)
		form_margin.add_theme_constant_override("margin_right", 34)
		form_margin.add_theme_constant_override("margin_bottom", 28)
		form_copy_label.visible = true
		form_copy_label.add_theme_font_size_override("font_size", 14)
		preview_note.visible = true
		preview_note.add_theme_font_size_override("font_size", 12)
		account.add_theme_font_size_override("font_size", 16)
		secret.add_theme_font_size_override("font_size", 16)
		error_label.add_theme_font_size_override("font_size", 13)
		enter_button.add_theme_font_size_override("font_size", 15)
		guest_button.add_theme_font_size_override("font_size", 15)
		if demo_link != null:
			demo_link.add_theme_font_size_override("font_size", 13)
		if clear_link != null:
			clear_link.add_theme_font_size_override("font_size", 13)
		music_button.add_theme_font_size_override("font_size", 12)
		if success_continue_button != null:
			success_continue_button.add_theme_font_size_override("font_size", 15)
		if success_back_button != null:
			success_back_button.add_theme_font_size_override("font_size", 15)
		success_title.add_theme_font_size_override("font_size", 28)
		success_copy.add_theme_font_size_override("font_size", 15)
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

func _toggle_music() -> void:
	ost.toggle_music()
	await get_tree().process_frame
	music_button.text = "音樂 · 關" if ost.is_music_paused() else "音樂 · 開"

func _complete(name: String, _guest: bool) -> void:
	if login_transitioning:
		return
	login_transitioning = true
	error_label.text = " "
	session_player_name = name
	GameState.player_name = session_player_name
	enter_button.disabled = true
	guest_button.disabled = true
	success_content.visible = false
	success_layer.visible = true
	success_layer.modulate.a = 1.0 if reduce_motion else 0.0
	if reduce_motion:
		get_tree().change_scene_to_file("res://scenes/prologue.tscn")
		return
	var transition := create_tween()
	transition.set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	transition.tween_property(success_layer, "modulate:a", 1.0, 0.44)
	transition.tween_callback(func() -> void:
		get_tree().change_scene_to_file("res://scenes/prologue.tscn")
	)

func _close_success() -> void:
	if reduce_motion:
		success_layer.visible = false
		return
	var tween := create_tween()
	tween.tween_property(success_layer, "modulate:a", 0.0, 0.24)
	tween.tween_callback(func() -> void: success_layer.visible = false)

func _go_to_game() -> void:
	GameState.player_name = session_player_name
	get_tree().change_scene_to_file("res://scenes/prologue.tscn")

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

func _title_gradient_material() -> ShaderMaterial:
	var shader := Shader.new()
	shader.code = """
shader_type canvas_item;
uniform vec4 color_top : source_color = vec4(1.000, 0.973, 0.910, 1.0);
uniform vec4 color_mid : source_color = vec4(0.851, 0.769, 0.608, 1.0);
uniform vec4 color_bot : source_color = vec4(0.592, 0.471, 0.278, 1.0);
uniform vec4 shadow_tint : source_color = vec4(0.020, 0.015, 0.015, 1.0);
uniform vec2 shadow_offset = vec2(0.004, 0.055);
uniform float shadow_strength : hint_range(0.0, 1.0) = 0.55;
void fragment() {
	vec4 glyph = texture(TEXTURE, UV);
	vec4 shade = texture(TEXTURE, UV - shadow_offset);
	float t = UV.y;
	vec3 grad;
	if (t < 0.05) {
		grad = color_top.rgb;
	} else if (t < 0.76) {
		grad = mix(color_top.rgb, color_mid.rgb, (t - 0.05) / 0.71);
	} else {
		grad = mix(color_mid.rgb, color_bot.rgb, (t - 0.76) / 0.24);
	}
	float shadow_a = shade.a * shadow_strength;
	COLOR = vec4(mix(shadow_tint.rgb, grad, glyph.a), max(glyph.a, shadow_a));
}
"""
	var material := ShaderMaterial.new()
	material.shader = shader
	return material

func _spacer(height: float) -> Control:
	var spacer := Control.new()
	spacer.custom_minimum_size.y = height
	return spacer
