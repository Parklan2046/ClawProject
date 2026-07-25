extends Node3D

const WORLD_SCRIPT = preload("res://scripts/prologue/prologue_world.gd")
const GAUGE_SCRIPT = preload("res://scripts/ui/timing_gauge.gd")
const OST_SCRIPT = preload("res://scripts/wuxia_ost.gd")
const TEXT := Color("#f1ede4")
const MUTED := Color("#a9a397")
const GOLD := Color("#d3b36f")
const RED := Color("#af3f35")
const INK := Color("#090b0f")

var world: Node3D
var ui_root: Control
var chapter_label: Label
var objective_label: Label
var dialogue_panel: PanelContainer
var speaker_label: Label
var dialogue_body: RichTextLabel
var continue_button: Button
var choice_panel: PanelContainer
var choice_title: Label
var choice_list: VBoxContainer
var inspect_panel: PanelContainer
var inspect_title: Label
var inspect_grid: GridContainer
var repair_panel: PanelContainer
var gauge: Control
var summary_panel: PanelContainer
var summary_content: VBoxContainer
var fade: ColorRect
var top_bar: ColorRect
var bottom_bar: ColorRect
var current_lines: Array = []
var current_line_index := -1
var after_lines := Callable()
var typing_tween: Tween
var inspected := {
	"coins": false,
	"steamer": false,
	"debt": false,
	"stove": false
}
var inspection_buttons: Dictionary = {}
var contract_result := ""
var repair_score := 0.0
var reduce_motion := false

func _ready() -> void:
	reduce_motion = _prefers_reduced_motion()
	world = WORLD_SCRIPT.new()
	world.name = "PrologueWorld"
	add_child(world)
	_build_ui()
	var ost := OST_SCRIPT.new()
	ost.volume_db = -12.0
	add_child(ost)
	get_viewport().size_changed.connect(_apply_layout)
	_apply_layout()
	GameState.reset_prologue()
	_start_modern_intro()

func _build_ui() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)

	ui_root = Control.new()
	ui_root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var app_theme := Theme.new()
	app_theme.default_font = load("res://assets/fonts/NotoSansTC-Variable.ttf")
	app_theme.default_font_size = 15
	ui_root.theme = app_theme
	layer.add_child(ui_root)

	var veil := ColorRect.new()
	veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	veil.color = Color(0.01, 0.015, 0.022, 0.12)
	veil.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_root.add_child(veil)

	top_bar = ColorRect.new()
	top_bar.color = Color(0.015, 0.018, 0.024, 0.96)
	top_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_root.add_child(top_bar)

	bottom_bar = ColorRect.new()
	bottom_bar.color = Color(0.015, 0.018, 0.024, 0.96)
	bottom_bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ui_root.add_child(bottom_bar)

	chapter_label = Label.new()
	chapter_label.text = "序章 00 · LAST ORDER"
	chapter_label.add_theme_font_size_override("font_size", 12)
	chapter_label.add_theme_color_override("font_color", GOLD)
	chapter_label.add_theme_constant_override("outline_size", 5)
	chapter_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.75))
	ui_root.add_child(chapter_label)

	objective_label = Label.new()
	objective_label.text = "目標｜撐過今晚"
	objective_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	objective_label.add_theme_font_size_override("font_size", 12)
	objective_label.add_theme_color_override("font_color", TEXT)
	objective_label.add_theme_constant_override("outline_size", 5)
	objective_label.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.75))
	ui_root.add_child(objective_label)

	dialogue_panel = PanelContainer.new()
	dialogue_panel.add_theme_stylebox_override("panel", _panel_style(Color(0.025, 0.030, 0.039, 0.95), Color(0.40, 0.37, 0.31, 0.9), 16, 1))
	ui_root.add_child(dialogue_panel)

	var dialogue_margin := MarginContainer.new()
	for side in ["margin_left", "margin_top", "margin_right", "margin_bottom"]:
		dialogue_margin.add_theme_constant_override(side, 22 if side != "margin_bottom" else 18)
	dialogue_panel.add_child(dialogue_margin)

	var dialogue_vbox := VBoxContainer.new()
	dialogue_vbox.add_theme_constant_override("separation", 9)
	dialogue_margin.add_child(dialogue_vbox)

	speaker_label = Label.new()
	speaker_label.text = "旁白"
	speaker_label.add_theme_font_size_override("font_size", 13)
	speaker_label.add_theme_color_override("font_color", GOLD)
	dialogue_vbox.add_child(speaker_label)

	dialogue_body = RichTextLabel.new()
	dialogue_body.bbcode_enabled = true
	dialogue_body.fit_content = true
	dialogue_body.scroll_active = false
	dialogue_body.custom_minimum_size.y = 68
	dialogue_body.add_theme_font_size_override("normal_font_size", 18)
	dialogue_body.add_theme_color_override("default_color", TEXT)
	dialogue_vbox.add_child(dialogue_body)

	continue_button = _button("繼續  ›", true)
	continue_button.custom_minimum_size = Vector2(132, 44)
	continue_button.size_flags_horizontal = Control.SIZE_SHRINK_END
	continue_button.pressed.connect(_advance_line)
	dialogue_vbox.add_child(continue_button)

	choice_panel = PanelContainer.new()
	choice_panel.visible = false
	choice_panel.add_theme_stylebox_override("panel", _panel_style(Color(0.025, 0.030, 0.039, 0.97), Color(0.45, 0.39, 0.28, 0.86), 16, 1))
	ui_root.add_child(choice_panel)
	var choice_margin := MarginContainer.new()
	choice_margin.add_theme_constant_override("margin_left", 20)
	choice_margin.add_theme_constant_override("margin_top", 18)
	choice_margin.add_theme_constant_override("margin_right", 20)
	choice_margin.add_theme_constant_override("margin_bottom", 20)
	choice_panel.add_child(choice_margin)
	var choice_vbox := VBoxContainer.new()
	choice_vbox.add_theme_constant_override("separation", 10)
	choice_margin.add_child(choice_vbox)
	choice_title = Label.new()
	choice_title.add_theme_font_size_override("font_size", 19)
	choice_title.add_theme_color_override("font_color", TEXT)
	choice_vbox.add_child(choice_title)
	choice_list = VBoxContainer.new()
	choice_list.add_theme_constant_override("separation", 8)
	choice_vbox.add_child(choice_list)

	inspect_panel = PanelContainer.new()
	inspect_panel.visible = false
	inspect_panel.add_theme_stylebox_override("panel", _panel_style(Color(0.025, 0.030, 0.039, 0.95), Color(0.45, 0.39, 0.28, 0.82), 16, 1))
	ui_root.add_child(inspect_panel)
	var inspect_margin := MarginContainer.new()
	inspect_margin.add_theme_constant_override("margin_left", 18)
	inspect_margin.add_theme_constant_override("margin_top", 16)
	inspect_margin.add_theme_constant_override("margin_right", 18)
	inspect_margin.add_theme_constant_override("margin_bottom", 18)
	inspect_panel.add_child(inspect_margin)
	var inspect_vbox := VBoxContainer.new()
	inspect_vbox.add_theme_constant_override("separation", 12)
	inspect_margin.add_child(inspect_vbox)
	inspect_title = Label.new()
	inspect_title.text = "調查屋內線索 · 0 / 4"
	inspect_title.add_theme_color_override("font_color", GOLD)
	inspect_title.add_theme_font_size_override("font_size", 16)
	inspect_vbox.add_child(inspect_title)
	inspect_grid = GridContainer.new()
	inspect_grid.columns = 2
	inspect_grid.add_theme_constant_override("h_separation", 8)
	inspect_grid.add_theme_constant_override("v_separation", 8)
	inspect_vbox.add_child(inspect_grid)

	var inspect_specs := [
		["coins", "十七文錢"],
		["steamer", "破裂蒸籠"],
		["debt", "王婆欠單"],
		["stove", "熄滅爐灶"]
	]
	for spec in inspect_specs:
		var button := _button(spec[1], false)
		button.custom_minimum_size = Vector2(155, 48)
		button.pressed.connect(_inspect.bind(spec[0]))
		inspect_grid.add_child(button)
		inspection_buttons[spec[0]] = button

	repair_panel = PanelContainer.new()
	repair_panel.visible = false
	repair_panel.add_theme_stylebox_override("panel", _panel_style(Color(0.025, 0.030, 0.039, 0.98), Color(0.55, 0.36, 0.19, 0.95), 16, 1))
	ui_root.add_child(repair_panel)
	var repair_margin := MarginContainer.new()
	repair_margin.add_theme_constant_override("margin_left", 22)
	repair_margin.add_theme_constant_override("margin_top", 18)
	repair_margin.add_theme_constant_override("margin_right", 22)
	repair_margin.add_theme_constant_override("margin_bottom", 20)
	repair_panel.add_child(repair_margin)
	var repair_vbox := VBoxContainer.new()
	repair_vbox.add_theme_constant_override("separation", 9)
	repair_margin.add_child(repair_vbox)
	var repair_title := Label.new()
	repair_title.text = "修復爐灶 · 清灰／補泥／試火"
	repair_title.add_theme_font_size_override("font_size", 20)
	repair_title.add_theme_color_override("font_color", TEXT)
	repair_vbox.add_child(repair_title)
	var repair_copy := Label.new()
	repair_copy.text = "前世知識只係方法，能否落到雙手，先係真正本事。"
	repair_copy.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	repair_copy.add_theme_color_override("font_color", MUTED)
	repair_vbox.add_child(repair_copy)
	gauge = GAUGE_SCRIPT.new()
	gauge.finished.connect(_repair_finished)
	repair_vbox.add_child(gauge)

	summary_panel = PanelContainer.new()
	summary_panel.visible = false
	summary_panel.add_theme_stylebox_override("panel", _panel_style(Color(0.025, 0.030, 0.039, 0.98), Color(0.63, 0.50, 0.28, 0.95), 18, 1))
	ui_root.add_child(summary_panel)
	var summary_margin := MarginContainer.new()
	summary_margin.add_theme_constant_override("margin_left", 28)
	summary_margin.add_theme_constant_override("margin_top", 24)
	summary_margin.add_theme_constant_override("margin_right", 28)
	summary_margin.add_theme_constant_override("margin_bottom", 24)
	summary_panel.add_child(summary_margin)
	summary_content = VBoxContainer.new()
	summary_content.add_theme_constant_override("separation", 13)
	summary_margin.add_child(summary_content)

	fade = ColorRect.new()
	fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	fade.color = Color(0.96, 0.91, 0.79, 0)
	fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	fade.z_index = 100
	ui_root.add_child(fade)

func _start_modern_intro() -> void:
	world.build_modern_restaurant()
	chapter_label.text = "序章 00 · LAST ORDER"
	objective_label.text = "目標｜撐過今晚"
	_run_lines([
		{"speaker": "旁白", "text": "凌晨三點十七分。最後一張訂單早已送出，雨仍然打在玻璃上。"},
		{"speaker": "手機通知", "text": "[color=#df776b]平台扣款：HK$18,420。供應商催款：最後期限。合伙人帳戶：已停用。[/color]"},
		{"speaker": "你", "text": "三年。由一間小廚房做到十二個外賣點……原來輸掉一盤生意，只需要一個晚上。"},
		{"speaker": "旁白", "text": "你望住枱面散亂的單據。失敗沒有帶走你最重要的東西——你仍記得自己如何由零開始。"}
	], _show_origin_choice)

func _show_origin_choice() -> void:
	dialogue_panel.visible = false
	objective_label.text = "選擇｜你帶到北宋的本事"
	var options: Array = []
	for id in ["chef", "brand", "logistics", "finance"]:
		var data: Dictionary = GameState.ORIGINS[id]
		options.append({
			"label": "%s｜%s" % [data.name, data.talent],
			"description": data.description,
			"action": _select_origin.bind(id)
		})
	_show_choices("前世留下的專長", options)

func _select_origin(id: String) -> void:
	GameState.origin_id = id
	choice_panel.visible = false
	var data: Dictionary = GameState.ORIGINS[id]
	_run_lines([
		{"speaker": "記憶", "text": "你記住了「[color=#d3b36f]%s[/color]」。技巧會消失，判斷不會。" % data.talent},
		{"speaker": "電話留言", "text": "『如果可以再嚟一次，你仲會唔會選擇做生意？』"}
	], _show_principle_choice)

func _show_principle_choice() -> void:
	dialogue_panel.visible = false
	objective_label.text = "選擇｜你會用甚麼方法翻身"
	_show_choices("面對第二次人生", [
		{"label": "仁義｜先保住人", "description": "人心比短期利潤重要。", "action": _select_principle.bind("benevolent")},
		{"label": "務實｜先令店活下去", "description": "不浪費，不逞強，逐步翻身。", "action": _select_principle.bind("pragmatic")},
		{"label": "冒險｜押上一次機會", "description": "高風險換取最快成長。", "action": _select_principle.bind("bold")},
		{"label": "權謀｜先看清所有人", "description": "情報、籌碼與退路同樣重要。", "action": _select_principle.bind("cunning")}
	])

func _select_principle(id: String) -> void:
	GameState.principle_id = id
	choice_panel.visible = false
	_run_lines([
		{"speaker": "你", "text": "如果命運肯畀第二次機會，我會用「[color=#d3b36f]%s[/color]」走到最後。" % GameState.principle_name()},
		{"speaker": "旁白", "text": "窗外一道白光撕開夜雨。手機墜地，蒸汽、車聲和心跳同時遠去。"},
		{"speaker": "？？？", "text": "大郎……大郎！你醒下啊！"}
	], _cross_to_song)

func _cross_to_song() -> void:
	dialogue_panel.visible = false
	var duration := 0.01 if reduce_motion else 0.85
	var tween := create_tween()
	tween.tween_property(fade, "color:a", 1.0, duration)
	tween.tween_callback(func() -> void:
		world.build_song_home()
		chapter_label.text = "序章 01 · 醒在死局"
		objective_label.text = "目標｜認清你的處境"
	)
	tween.tween_property(fade, "color", Color(0.05, 0.035, 0.025, 0), duration)
	tween.tween_callback(_start_song_intro)

func _start_song_intro() -> void:
	_run_lines([
		{"speaker": "旁白", "text": "霉木、麵粉、冷灰。你在一張硬木床上醒來，胸口像被另一個人的一生壓住。"},
		{"speaker": "陌生記憶", "text": "陽谷縣。賣炊餅。武家大郎。妻，潘金蓮。弟，武松。"},
		{"speaker": "你", "text": "武大郎……如果呢個故事照原本行落去，我連自己點死都知道。"},
		{"speaker": "旁白", "text": "屋內每一件東西都在提醒你：死局未到，但貧窮已經先一步收網。"}
	], _start_inspection)

func _start_inspection() -> void:
	dialogue_panel.visible = false
	inspect_panel.visible = true
	objective_label.text = "調查｜屋內線索 0 / 4"
	world.reset_camera()

func _inspect(id: String) -> void:
	if inspected[id]:
		return
	inspected[id] = true
	inspect_panel.visible = false
	world.focus(id)
	var content: Array = {
		"coins": ["十七文錢", "錢袋輕得近乎侮辱。十七文，連一袋好麵粉都買唔到。"],
		"steamer": ["破裂蒸籠", "竹篾斷了兩處，邊緣積滿舊麵粉。修得好，今日仍可開爐。"],
		"debt": ["王婆欠單", "紙上寫住三百二十文，利息每七日再加一成。落款是王婆的指印。"],
		"stove": ["熄滅爐灶", "爐膛堵塞，泥縫裂開。不是不能用，只是以前的武大郎沒有時間，也沒有方法。"]
	}[id]
	_run_lines([
		{"speaker": content[0], "text": content[1]}
	], _after_inspection)

func _after_inspection() -> void:
	world.reset_camera()
	var count := 0
	for value in inspected.values():
		if value:
			count += 1
	for id in inspection_buttons:
		var button: Button = inspection_buttons[id]
		button.disabled = inspected[id]
		if inspected[id]:
			button.text = "已調查 · " + button.text.replace("已調查 · ", "")
	inspect_title.text = "調查屋內線索 · %d / 4" % count
	objective_label.text = "調查｜屋內線索 %d / 4" % count
	if count >= 4:
		_start_pan_scene()
	else:
		dialogue_panel.visible = false
		inspect_panel.visible = true

func _start_pan_scene() -> void:
	inspect_panel.visible = false
	objective_label.text = "對話｜潘金蓮"
	_run_lines([
		{"speaker": "潘金蓮", "text": "你由朝早醒到而家，先數錢，再睇帳，仲識得檢查爐膛。"},
		{"speaker": "潘金蓮", "text": "大郎，你以前只會叫我放心。今日，你第一次真係想辦法。"},
		{"speaker": "你", "text": "我唔會叫你再等運氣。呢間舖要重新開，但我需要你本帳，同埋你對街坊嘅了解。"},
		{"speaker": "潘金蓮", "text": "可以。但我要做掌櫃，唔係企在門口替你招客。白紙黑字，你敢唔敢？"}
	], _show_contract_choice)

func _show_contract_choice() -> void:
	dialogue_panel.visible = false
	_show_choices("共同掌櫃契", [
		{"label": "簽下平分契", "description": "店舖、利潤與決策各佔一半。", "action": _choose_contract.bind("equal")},
		{"label": "先試做七日", "description": "暫緩分權，但給潘金蓮完整帳目。", "action": _choose_contract.bind("trial")},
		{"label": "拒絕分權", "description": "保留全部收入，她會另尋自己的路。", "action": _choose_contract.bind("refuse")}
	])

func _choose_contract(id: String) -> void:
	contract_result = id
	choice_panel.visible = false
	if id == "equal":
		GameState.relationship.pan_trust += 15
		GameState.relationship.pan_respect += 10
		GameState.set_flag("pan_equal_partner", true)
		_run_lines([
			{"speaker": "你", "text": "一半唔係我分畀你。由今日開始，本來就有一半係你。"},
			{"speaker": "潘金蓮", "text": "好。咁我就睇下，今日呢個武大郎可以行到幾遠。"}
		], _start_repair_intro)
	elif id == "trial":
		GameState.relationship.pan_trust += 5
		GameState.relationship.pan_respect += 4
		GameState.set_flag("pan_trial_partner", true)
		_run_lines([
			{"speaker": "你", "text": "七日。所有數目你都可以睇，做得成，我哋再正式落契。"},
			{"speaker": "潘金蓮", "text": "至少你今次冇叫我盲目信你。七日，我記住。"}
		], _start_repair_intro)
	else:
		GameState.relationship.pan_trust -= 10
		GameState.relationship.pan_respect -= 4
		GameState.set_flag("pan_independent_stall", true)
		_run_lines([
			{"speaker": "你", "text": "店係武家嘅。我可以畀工錢，但唔會分權。"},
			{"speaker": "潘金蓮", "text": "明白。咁你做你嘅餅，我亦會為自己留一條路。"}
		], _start_repair_intro)

func _start_repair_intro() -> void:
	world.focus("stove")
	objective_label.text = "玩法｜修復爐灶"
	_run_lines([
		{"speaker": "旁白", "text": "說話可以改變關係，雙手先可以改變今日。你捲起衣袖，清走爐灰，再用濕泥補上裂縫。"},
		{"speaker": "潘金蓮", "text": "火候過咗，泥會爆；唔夠火，今日就開唔到爐。你有三次機會。"}
	], _start_repair_game)

func _start_repair_game() -> void:
	dialogue_panel.visible = false
	repair_panel.visible = true
	gauge.start(3)

func _repair_finished(score: float) -> void:
	repair_score = score
	repair_panel.visible = false
	world.reset_camera()
	var result_text := ""
	if score >= 0.82:
		GameState.set_flag("stove_quality", "master")
		GameState.reputation += 2
		result_text = "泥縫在火光中逐漸收實，爐膛發出均勻低鳴。呢個爐比以前更穩、更慳柴。"
	elif score >= 0.52:
		GameState.set_flag("stove_quality", "steady")
		GameState.reputation += 1
		result_text = "火焰終於穩定。爐灶仍然粗陋，但足以蒸出今日第一籠餅。"
	else:
		GameState.set_flag("stove_quality", "fragile")
		result_text = "裂縫勉強封住，火仍從旁邊漏出。今日可以開爐，但之後一定要重新修理。"
	GameState.set_flag("prologue_complete", true)
	GameState.set_flag("contract_result", contract_result)
	GameState.set_flag("repair_score", repair_score)
	GameState.checkpoint = "chapter_01_first_fire"
	SaveManager.save_game()
	_run_lines([
		{"speaker": "修爐結果", "text": result_text},
		{"speaker": "潘金蓮", "text": "火着咗。"},
		{"speaker": "你", "text": "唔止個爐。由今日開始，成條命都要重新着一次。"},
		{"speaker": "旁白", "text": "窗外天色微亮。陽谷縣仍未知道，一間只有十七文本錢的炊餅店，已經偏離了原本的命數。"}
	], _show_summary)

func _show_summary() -> void:
	dialogue_panel.visible = false
	chapter_label.text = "序章完成 · 死局重生"
	objective_label.text = "下一章｜一餅逆命"
	for child in summary_content.get_children():
		summary_content.remove_child(child)
		child.queue_free()
	var seal := Label.new()
	seal.text = "命"
	seal.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	seal.add_theme_font_size_override("font_size", 28)
	seal.add_theme_color_override("font_color", TEXT)
	seal.add_theme_stylebox_override("normal", _panel_style(RED, RED, 8, 0))
	seal.custom_minimum_size = Vector2(54, 54)
	seal.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	summary_content.add_child(seal)
	var title := Label.new()
	title.text = "序章完成 · 死局重生"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 28)
	title.add_theme_color_override("font_color", TEXT)
	summary_content.add_child(title)
	var summary := RichTextLabel.new()
	summary.bbcode_enabled = true
	summary.fit_content = true
	summary.scroll_active = false
	summary.custom_minimum_size.y = 132
	summary.text = "[center]前世專長　[color=#d3b36f]%s[/color]\n行事信念　[color=#d3b36f]%s[/color]\n掌櫃契約　[color=#d3b36f]%s[/color]\n修爐評價　[color=#d3b36f]%s[/color]\n\n存檔已寫入。下一次命運選擇，將由第一籠炊餅開始。[/center]" % [
		GameState.origin_name(),
		GameState.principle_name(),
		_contract_name(),
		_repair_rank()
	]
	summary.add_theme_font_size_override("normal_font_size", 16)
	summary.add_theme_color_override("default_color", MUTED)
	summary_content.add_child(summary)
	var chapter_button := _button("進入第一章 · 一餅逆命", true)
	chapter_button.disabled = true
	chapter_button.tooltip_text = "第一章將在下一個製作階段開放"
	summary_content.add_child(chapter_button)
	var replay_button := _button("重新體驗序章", false)
	replay_button.pressed.connect(func() -> void: get_tree().reload_current_scene())
	summary_content.add_child(replay_button)
	var login_button := _button("返回登入頁", false)
	login_button.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://scenes/login.tscn"))
	summary_content.add_child(login_button)
	summary_panel.visible = true

func _run_lines(lines: Array, finished_callback: Callable) -> void:
	current_lines = lines
	current_line_index = -1
	after_lines = finished_callback
	dialogue_panel.visible = true
	continue_button.visible = true
	choice_panel.visible = false
	inspect_panel.visible = false
	_advance_line()

func _advance_line() -> void:
	if dialogue_body.visible_ratio < 0.995:
		if typing_tween and typing_tween.is_valid():
			typing_tween.kill()
		dialogue_body.visible_ratio = 1.0
		return
	current_line_index += 1
	if current_line_index >= current_lines.size():
		dialogue_panel.visible = false
		if after_lines.is_valid():
			after_lines.call()
		return
	var line: Dictionary = current_lines[current_line_index]
	speaker_label.text = str(line.get("speaker", "旁白"))
	dialogue_body.text = str(line.get("text", ""))
	dialogue_body.visible_ratio = 1.0 if reduce_motion else 0.0
	continue_button.text = "繼續  ›" if current_line_index < current_lines.size() - 1 else "確認  ›"
	if not reduce_motion:
		var plain_length := dialogue_body.get_parsed_text().length()
		var duration := clampf(plain_length * 0.018, 0.35, 1.8)
		typing_tween = create_tween()
		typing_tween.tween_property(dialogue_body, "visible_ratio", 1.0, duration)

func _show_choices(title: String, options: Array) -> void:
	choice_title.text = title
	for child in choice_list.get_children():
		choice_list.remove_child(child)
		child.queue_free()
	for option in options:
		var button := _button("%s\n%s" % [option.label, option.description], false)
		button.custom_minimum_size.y = 60
		button.alignment = HORIZONTAL_ALIGNMENT_LEFT
		button.pressed.connect(option.action)
		choice_list.add_child(button)
	choice_panel.visible = true

func _contract_name() -> String:
	return {
		"equal": "平分掌櫃",
		"trial": "七日試約",
		"refuse": "各行其路"
	}.get(contract_result, "未定")

func _repair_rank() -> String:
	if repair_score >= 0.82:
		return "爐火純熟"
	if repair_score >= 0.52:
		return "穩定可用"
	return "勉強點火"

func _apply_layout() -> void:
	if ui_root == null:
		return
	var size_value: Vector2 = get_viewport().get_visible_rect().size
	var mobile: bool = size_value.x < 720.0
	top_bar.position = Vector2.ZERO
	top_bar.size = Vector2(size_value.x, 24 if mobile else 30)
	bottom_bar.position = Vector2(0, size_value.y - (20 if mobile else 26))
	bottom_bar.size = Vector2(size_value.x, 20 if mobile else 26)
	var pad := 18.0 if mobile else clampf(size_value.x * 0.045, 40.0, 72.0)
	chapter_label.position = Vector2(pad, 38 if mobile else 48)
	chapter_label.size = Vector2(size_value.x * 0.55, 28)
	objective_label.position = Vector2(size_value.x * 0.48, 38 if mobile else 48)
	objective_label.size = Vector2(size_value.x * 0.52 - pad, 28)
	if mobile:
		dialogue_panel.position = Vector2(pad, size_value.y - 260)
		dialogue_panel.size = Vector2(size_value.x - pad * 2, 224)
		dialogue_body.add_theme_font_size_override("normal_font_size", 16)
		choice_panel.position = Vector2(pad, maxf(86, size_value.y * 0.16))
		choice_panel.size = Vector2(size_value.x - pad * 2, minf(448, size_value.y - 116))
		inspect_panel.position = Vector2(pad, size_value.y - 260)
		inspect_panel.size = Vector2(size_value.x - pad * 2, 224)
		repair_panel.position = Vector2(pad, size_value.y - 300)
		repair_panel.size = Vector2(size_value.x - pad * 2, 264)
		gauge.custom_minimum_size = Vector2(size_value.x - pad * 2 - 44, 88)
		summary_panel.position = Vector2(pad, 82)
		summary_panel.size = Vector2(size_value.x - pad * 2, size_value.y - 118)
	else:
		dialogue_panel.position = Vector2(pad, size_value.y - 260)
		dialogue_panel.size = Vector2(minf(860, size_value.x * 0.62), 206)
		dialogue_body.add_theme_font_size_override("normal_font_size", 18)
		choice_panel.position = Vector2(size_value.x - minf(500, size_value.x * 0.38) - pad, 108)
		choice_panel.size = Vector2(minf(500, size_value.x * 0.38), minf(530, size_value.y - 180))
		inspect_panel.position = Vector2(size_value.x - 415 - pad, size_value.y - 270)
		inspect_panel.size = Vector2(415, 216)
		repair_panel.position = Vector2(size_value.x - minf(560, size_value.x * 0.42) - pad, size_value.y - 330)
		repair_panel.size = Vector2(minf(560, size_value.x * 0.42), 276)
		gauge.custom_minimum_size = Vector2(minf(500, size_value.x * 0.38), 88)
		var summary_width := minf(520, size_value.x - pad * 2)
		summary_panel.position = Vector2((size_value.x - summary_width) * 0.5, 105)
		summary_panel.size = Vector2(summary_width, minf(620, size_value.y - 160))

func _button(label: String, primary: bool) -> Button:
	var button := Button.new()
	button.text = label
	button.custom_minimum_size = Vector2(0, 50)
	button.add_theme_font_size_override("font_size", 14)
	button.add_theme_color_override("font_color", TEXT)
	button.add_theme_color_override("font_hover_color", TEXT)
	button.add_theme_color_override("font_pressed_color", TEXT)
	button.add_theme_color_override("font_disabled_color", Color(0.55, 0.55, 0.55, 0.7))
	if primary:
		button.add_theme_stylebox_override("normal", _panel_style(RED, RED, 10, 0))
		button.add_theme_stylebox_override("hover", _panel_style(Color("#c14b40"), Color("#c14b40"), 10, 0))
		button.add_theme_stylebox_override("pressed", _panel_style(Color("#873029"), Color("#873029"), 10, 0))
	else:
		button.add_theme_stylebox_override("normal", _panel_style(Color("#171b21"), Color("#3a414b"), 10, 1))
		button.add_theme_stylebox_override("hover", _panel_style(Color("#242a33"), Color("#8c7448"), 10, 1))
		button.add_theme_stylebox_override("pressed", _panel_style(Color("#0f1217"), Color("#8c7448"), 10, 1))
		button.add_theme_stylebox_override("disabled", _panel_style(Color("#111419"), Color("#292e35"), 10, 1))
	return button

func _panel_style(fill: Color, border: Color, radius: int, border_width: int) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(border_width)
	style.set_corner_radius_all(radius)
	return style

func _prefers_reduced_motion() -> bool:
	if not OS.has_feature("web"):
		return false
	var result: Variant = JavaScriptBridge.eval("window.matchMedia('(prefers-reduced-motion: reduce)').matches")
	return bool(result)
