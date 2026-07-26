extends Control

const TEXT := Color("#f1ede4")
const MUTED := Color("#aaa59b")
const GOLD := Color("#d3b36f")
const RED := Color("#c84a40")
const BACKGROUND := Color("#0b0e13")

var days: Array = []
var current_day: Dictionary = {}
var day_start_snapshot: Dictionary = {}
var current_lines: Array = []
var current_line_index := -1
var after_lines := Callable()
var typing_tween: Tween
var reduce_motion := false

var page_margin: MarginContainer
var chapter_label: Label
var objective_label: Label
var stats_label: Label
var phase_label: Label
var speaker_label: Label
var dialogue_body: RichTextLabel
var button_scroll: ScrollContainer
var button_list: VBoxContainer
var save_label: Label

func _ready() -> void:
	reduce_motion = _prefers_reduced_motion()
	days = _build_days()
	var app_theme := Theme.new()
	app_theme.default_font = load("res://assets/fonts/NotoSansTC-Variable.ttf")
	app_theme.default_font_size = 16
	theme = app_theme
	_build_plain_ui()
	get_viewport().size_changed.connect(_apply_layout)
	_apply_layout()
	if GameState.chapter != 1 or GameState.chapter_day < 1:
		GameState.begin_chapter_one()
		SaveManager.save_game()
	call_deferred("_start_day")

func _build_plain_ui() -> void:
	var background := ColorRect.new()
	background.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	background.color = BACKGROUND
	background.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(background)

	page_margin = MarginContainer.new()
	page_margin.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(page_margin)

	var page := VBoxContainer.new()
	page.add_theme_constant_override("separation", 12)
	page_margin.add_child(page)

	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 12)
	page.add_child(header)

	chapter_label = Label.new()
	chapter_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	chapter_label.add_theme_font_size_override("font_size", 18)
	chapter_label.add_theme_color_override("font_color", GOLD)
	header.add_child(chapter_label)

	objective_label = Label.new()
	objective_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	objective_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	objective_label.add_theme_font_size_override("font_size", 16)
	objective_label.add_theme_color_override("font_color", TEXT)
	header.add_child(objective_label)

	stats_label = Label.new()
	stats_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	stats_label.add_theme_font_size_override("font_size", 16)
	stats_label.add_theme_color_override("font_color", MUTED)
	page.add_child(stats_label)

	var rule := HSeparator.new()
	page.add_child(rule)

	phase_label = Label.new()
	phase_label.add_theme_font_size_override("font_size", 15)
	phase_label.add_theme_color_override("font_color", RED)
	page.add_child(phase_label)

	speaker_label = Label.new()
	speaker_label.add_theme_font_size_override("font_size", 17)
	speaker_label.add_theme_color_override("font_color", GOLD)
	page.add_child(speaker_label)

	dialogue_body = RichTextLabel.new()
	dialogue_body.bbcode_enabled = true
	dialogue_body.fit_content = false
	dialogue_body.scroll_active = true
	dialogue_body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	dialogue_body.custom_minimum_size.y = 180
	dialogue_body.add_theme_font_size_override("normal_font_size", 19)
	dialogue_body.add_theme_color_override("default_color", TEXT)
	page.add_child(dialogue_body)

	button_scroll = ScrollContainer.new()
	button_scroll.custom_minimum_size.y = 230
	button_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page.add_child(button_scroll)

	button_list = VBoxContainer.new()
	button_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button_list.add_theme_constant_override("separation", 9)
	button_scroll.add_child(button_list)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 10)
	page.add_child(footer)

	save_label = Label.new()
	save_label.text = "進度會在每日結算後保存"
	save_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	save_label.add_theme_font_size_override("font_size", 14)
	save_label.add_theme_color_override("font_color", MUTED)
	footer.add_child(save_label)

	var exit_button := Button.new()
	exit_button.text = "返回登入頁"
	exit_button.custom_minimum_size = Vector2(120, 42)
	exit_button.add_theme_font_size_override("font_size", 15)
	exit_button.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://scenes/login.tscn"))
	footer.add_child(exit_button)

func _start_day() -> void:
	if GameState.chapter_day > days.size():
		_show_chapter_summary()
		return
	current_day = days[GameState.chapter_day - 1]
	var supply_key := "chapter_01_supply_day_%02d" % GameState.chapter_day
	if not bool(GameState.get_flag(supply_key, false)):
		GameState.flour += 1
		GameState.set_flag(supply_key, true)
		SaveManager.save_game()
	day_start_snapshot = _snapshot()
	chapter_label.text = "第一章 · 一餅逆命　DAY %02d / 10" % GameState.chapter_day
	objective_label.text = str(current_day.objective)
	_update_stats()
	phase_label.text = "晨間｜今日局勢"
	_run_lines(current_day.intro, _show_work_choice)

func _show_work_choice() -> void:
	phase_label.text = "日間｜選擇今日重點"
	_show_choices(
		"今日只有一次主要行動。你的準備會改變黃昏事件的解法。",
		current_day.work,
		"work"
	)

func _show_event() -> void:
	phase_label.text = "黃昏｜關鍵事件"
	_run_lines(current_day.event_intro, _show_event_choice)

func _show_event_choice() -> void:
	phase_label.text = "黃昏｜作出決定"
	_show_choices(
		str(current_day.event_prompt),
		current_day.event,
		"event"
	)

func _show_night() -> void:
	phase_label.text = "夜間｜結算"
	var delta := _delta_text(day_start_snapshot, _snapshot())
	var lines: Array = current_day.night.duplicate(true)
	lines.push_front({
		"speaker": "今日結算",
		"text": delta
	})
	_run_lines(lines, _show_day_complete_button)

func _show_day_complete_button() -> void:
	speaker_label.text = "系統"
	dialogue_body.text = "今日的經營、人物事件與結算已全部完成。完成每日循環後，下一日才會解鎖。"
	dialogue_body.visible_ratio = 1.0
	_clear_buttons()
	var button := _make_button(
		"完成第 %d 日 · %s" % [GameState.chapter_day, "進入下一日" if GameState.chapter_day < 10 else "查看第一章結果"],
		true
	)
	button.pressed.connect(_complete_day)
	button_list.add_child(button)

func _complete_day() -> void:
	GameState.set_flag("chapter_01_day_%02d_complete" % GameState.chapter_day, true)
	if GameState.chapter_day >= 10:
		GameState.set_flag("chapter_01_complete", true)
		GameState.checkpoint = "chapter_01_complete"
		SaveManager.save_game()
		_show_chapter_summary()
		return
	GameState.chapter_day += 1
	GameState.checkpoint = "chapter_01_day_%02d" % GameState.chapter_day
	SaveManager.save_game()
	save_label.text = "第 %d 日已保存" % (GameState.chapter_day - 1)
	_start_day()

func _show_chapter_summary() -> void:
	current_day = {}
	chapter_label.text = "第一章完成 · 一餅逆命"
	objective_label.text = "燈會之後"
	phase_label.text = "章末結算"
	var score: int = (
		int(GameState.reputation)
		+ int(GameState.intel)
		+ int(GameState.relationship.pan_trust / 2.0)
		+ int(GameState.relationship.wu_trust)
		+ maxi(0, 30 - int(GameState.debt))
	)
	var rank := "勉強守住武家"
	var route := "流動小販線"
	if score >= 45:
		rank = "完美逆命"
		route = "武家共同掌櫃線"
	elif score >= 28:
		rank = "清河立足"
		route = "武家炊餅品牌線"
	GameState.set_flag("chapter_01_rank", rank)
	GameState.set_flag("chapter_02_route", route)
	SaveManager.save_game()
	speaker_label.text = rank
	dialogue_body.text = (
		"[font_size=24][color=#d3b36f]%s[/color][/font_size]\n\n"
		+ "十日循環全部完成。\n"
		+ "銅錢：%d　麵粉：%d　債務：%d\n"
		+ "聲望：%d　情報：%d　西門慶警戒：%d\n"
		+ "潘金蓮信任：%d　武松信任：%d\n\n"
		+ "第二章起始路線：[color=#d3b36f]%s[/color]\n"
		+ "第二章《一鍋江湖》將在後續製作階段開放。"
	) % [
		rank,
		GameState.copper,
		GameState.flour,
		GameState.debt,
		GameState.reputation,
		GameState.intel,
		GameState.ximen_alert,
		GameState.relationship.pan_trust,
		GameState.relationship.wu_trust,
		route
	]
	dialogue_body.visible_ratio = 1.0
	_clear_buttons()
	var locked_button := _make_button("第二章 · 一鍋江湖（尚未開放）", true)
	locked_button.disabled = true
	button_list.add_child(locked_button)
	var login_button := _make_button("返回登入頁", false)
	login_button.pressed.connect(func() -> void: get_tree().change_scene_to_file("res://scenes/login.tscn"))
	button_list.add_child(login_button)

func _run_lines(lines: Array, finished_callback: Callable) -> void:
	current_lines = lines
	current_line_index = -1
	after_lines = finished_callback
	_advance_line()

func _advance_line() -> void:
	if dialogue_body.visible_ratio < 0.995:
		if typing_tween and typing_tween.is_valid():
			typing_tween.kill()
		dialogue_body.visible_ratio = 1.0
		return
	current_line_index += 1
	if current_line_index >= current_lines.size():
		if after_lines.is_valid():
			after_lines.call()
		return
	var line: Dictionary = current_lines[current_line_index]
	speaker_label.text = str(line.get("speaker", "旁白"))
	dialogue_body.text = str(line.get("text", ""))
	dialogue_body.visible_ratio = 1.0 if reduce_motion else 0.0
	_clear_buttons()
	var button_text := "繼續" if current_line_index < current_lines.size() - 1 else "確認"
	var button := _make_button(button_text, true)
	button.pressed.connect(_advance_line)
	button_list.add_child(button)
	if not reduce_motion:
		var duration := clampf(dialogue_body.get_parsed_text().length() * 0.014, 0.25, 1.25)
		typing_tween = create_tween()
		typing_tween.tween_property(dialogue_body, "visible_ratio", 1.0, duration)

func _show_choices(prompt: String, options: Array, stage: String) -> void:
	speaker_label.text = "你的選擇"
	dialogue_body.text = prompt
	dialogue_body.visible_ratio = 1.0
	_clear_buttons()
	for option: Dictionary in options:
		var availability := _option_availability(option)
		var button_text := "%s\n%s" % [option.label, option.description]
		if not availability.ok:
			button_text += "\n[未達條件：%s]" % availability.reason
		var button := _make_button(button_text, false)
		button.disabled = not availability.ok
		button.pressed.connect(_select_option.bind(option, stage))
		button_list.add_child(button)

func _select_option(option: Dictionary, stage: String) -> void:
	_apply_effects(option.get("effects", {}))
	GameState.set_flag(
		"chapter_01_day_%02d_%s_choice" % [GameState.chapter_day, stage],
		str(option.get("id", "unknown"))
	)
	_update_stats()
	var next := _show_event if stage == "work" else _show_night
	_run_lines(option.result, next)

func _apply_effects(effects: Dictionary) -> void:
	for key: String in effects:
		var value: Variant = effects[key]
		match key:
			"copper":
				GameState.copper += int(value)
			"flour":
				GameState.flour += int(value)
			"debt":
				GameState.debt += int(value)
			"reputation":
				GameState.reputation += int(value)
			"intel":
				GameState.intel += int(value)
			"ximen_alert":
				GameState.ximen_alert += int(value)
			"pan_trust", "pan_respect", "li_interest", "chunmei_leverage", "yunge_loyalty", "wu_trust":
				GameState.relationship[key] = int(GameState.relationship.get(key, 0)) + int(value)
			"flags":
				for flag_key: String in value:
					GameState.set_flag(flag_key, value[flag_key])
	GameState.copper = maxi(0, GameState.copper)
	GameState.flour = maxi(0, GameState.flour)
	GameState.debt = maxi(0, GameState.debt)
	GameState.intel = maxi(0, GameState.intel)
	GameState.ximen_alert = maxi(0, GameState.ximen_alert)

func _option_availability(option: Dictionary) -> Dictionary:
	var requirements: Dictionary = option.get("requires", {})
	for key: String in requirements:
		var needed := int(requirements[key])
		var actual := 0
		var label := key
		match key:
			"copper":
				actual = GameState.copper
				label = "銅錢 %d" % needed
			"flour":
				actual = GameState.flour
				label = "麵粉 %d" % needed
			"intel":
				actual = GameState.intel
				label = "情報 %d" % needed
			"reputation":
				actual = GameState.reputation
				label = "聲望 %d" % needed
			"pan_trust", "pan_respect", "li_interest", "chunmei_leverage", "yunge_loyalty", "wu_trust":
				actual = int(GameState.relationship.get(key, 0))
				label = "%s %d" % [_relationship_name(key), needed]
		if actual < needed:
			return {"ok": false, "reason": label}
	return {"ok": true, "reason": ""}

func _update_stats() -> void:
	stats_label.text = (
		"銅錢 %d　｜　麵粉 %d　｜　債務 %d　｜　聲望 %d　｜　情報 %d\n"
		+ "潘金蓮信任 %d　｜　武松信任 %d　｜　西門慶警戒 %d"
	) % [
		GameState.copper,
		GameState.flour,
		GameState.debt,
		GameState.reputation,
		GameState.intel,
		GameState.relationship.pan_trust,
		GameState.relationship.wu_trust,
		GameState.ximen_alert
	]

func _snapshot() -> Dictionary:
	return {
		"copper": GameState.copper,
		"flour": GameState.flour,
		"debt": GameState.debt,
		"reputation": GameState.reputation,
		"intel": GameState.intel,
		"pan_trust": GameState.relationship.pan_trust,
		"wu_trust": GameState.relationship.wu_trust
	}

func _delta_text(before: Dictionary, after: Dictionary) -> String:
	var parts: Array[String] = []
	var names := {
		"copper": "銅錢",
		"flour": "麵粉",
		"debt": "債務",
		"reputation": "聲望",
		"intel": "情報",
		"pan_trust": "潘金蓮信任",
		"wu_trust": "武松信任"
	}
	for key: String in names:
		var delta := int(after[key]) - int(before[key])
		if delta != 0:
			parts.append("%s %s%d" % [names[key], "+" if delta > 0 else "", delta])
	if parts.is_empty():
		return "今日沒有數值變化，但你作出的決定已被記錄。"
	return "今日變化：" + "　｜　".join(parts)

func _relationship_name(key: String) -> String:
	return {
		"pan_trust": "潘金蓮信任",
		"pan_respect": "潘金蓮敬重",
		"li_interest": "李瓶兒關係",
		"chunmei_leverage": "龐春梅合作",
		"yunge_loyalty": "鄆哥忠誠",
		"wu_trust": "武松信任"
	}.get(key, key)

func _clear_buttons() -> void:
	for child in button_list.get_children():
		button_list.remove_child(child)
		child.queue_free()
	button_scroll.scroll_vertical = 0

func _make_button(label: String, primary: bool) -> Button:
	var button := Button.new()
	button.text = label
	button.custom_minimum_size = Vector2(0, 58 if primary else 68)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.add_theme_font_size_override("font_size", 16)
	button.alignment = HORIZONTAL_ALIGNMENT_LEFT if not primary else HORIZONTAL_ALIGNMENT_CENTER
	return button

func _apply_layout() -> void:
	if page_margin == null:
		return
	var size_value := get_viewport().get_visible_rect().size
	var mobile := size_value.x < 760
	var side := 16 if mobile else maxi(32, int((size_value.x - 1080.0) * 0.5))
	page_margin.add_theme_constant_override("margin_left", side)
	page_margin.add_theme_constant_override("margin_right", side)
	page_margin.add_theme_constant_override("margin_top", 18 if mobile else 28)
	page_margin.add_theme_constant_override("margin_bottom", 14 if mobile else 22)
	chapter_label.add_theme_font_size_override("font_size", 16 if mobile else 18)
	objective_label.add_theme_font_size_override("font_size", 14 if mobile else 16)
	dialogue_body.add_theme_font_size_override("normal_font_size", 18 if mobile else 19)
	button_scroll.custom_minimum_size.y = 250 if mobile else 230

func _prefers_reduced_motion() -> bool:
	if not OS.has_feature("web"):
		return false
	var value: Variant = JavaScriptBridge.eval("window.matchMedia('(prefers-reduced-motion: reduce)').matches")
	return bool(value)

func _line(speaker: String, text: String) -> Dictionary:
	return {"speaker": speaker, "text": text}

func _choice(
	id: String,
	label: String,
	description: String,
	effects: Dictionary,
	result: Array,
	requires: Dictionary = {}
) -> Dictionary:
	return {
		"id": id,
		"label": label,
		"description": description,
		"effects": effects,
		"result": result,
		"requires": requires
	}

func _day(
	title: String,
	objective: String,
	intro: Array,
	work: Array,
	event_intro: Array,
	event_prompt: String,
	event: Array,
	night: Array
) -> Dictionary:
	return {
		"title": title,
		"objective": objective,
		"intro": intro,
		"work": work,
		"event_intro": event_intro,
		"event_prompt": event_prompt,
		"event": event,
		"night": night
	}

func _build_days() -> Array:
	return [
		_day(
			"醒在武家",
			"賣出第一籠炊餅",
			[
				_line("旁白", "天剛亮，修好的爐仍帶餘溫。桌上只有十七文、幾份麵粉，以及一張三十貫的可疑欠單。"),
				_line("潘金蓮", "爐火救得返，未必代表間屋救得返。王婆話今日再來收第一期。"),
				_line("你", "先讓第一籠餅出門。只要有人肯買，死局就有第一條裂縫。")
			],
			[
				_choice("steady_batch", "蒸一籠平價炊餅", "穩定開市，先賺回流動銅錢。", {"flour": -1, "copper": 5, "reputation": 1}, [
					_line("旁白", "第一籠炊餅不華麗，但熱氣和麥香令幾名早起腳夫停下腳步。"),
					_line("潘金蓮", "至少今日有人記得，武家個爐仲着住。")
				], {"flour": 1}),
				_choice("pan_package", "與潘金蓮改良包裝", "少賣一些，換取更好的口碑和信任。", {"flour": -1, "copper": 3, "reputation": 2, "pan_trust": 2, "pan_respect": 1}, [
					_line("潘金蓮", "用乾淨竹紙包好，再印個紅色『武』字。平凡嘅餅，都可以有名有姓。"),
					_line("你", "由今日開始，賣的不只是飽肚，還有武家的招牌。")
				], {"flour": 1}),
				_choice("cheap_volume", "低價多賣", "消耗較多麵粉，快速吸引街坊。", {"flour": -2, "copper": 7, "reputation": 2}, [
					_line("旁白", "你將價格壓到全街最低，一個上午便清掉兩籠。"),
					_line("潘金蓮", "客係多咗，但呢個價唔可以日日做。")
				], {"flour": 2})
			],
			[
				_line("王婆", "大郎，欠單寫得清清楚楚。今日交三貫，唔係就收你個爐。"),
				_line("旁白", "她把欠單拍在桌上。紙是真的，手印也像是真的，但墨色似乎太新。")
			],
			"第一日的收入應該用來還債，還是先追查欠單？",
			[
				_choice("inspect_debt", "檢查欠單墨跡", "保留現金，開始建立偽造欠單的證據。", {"intel": 2, "pan_respect": 1, "ximen_alert": 1}, [
					_line("你", "紙放舊了，墨卻是三日內才寫。王婆，這張單到底從哪裡來？"),
					_line("王婆", "識幾隻字就當自己判官？十日後我再來。")
				]),
				_choice("pay_deposit", "先交部分訂金", "降低債務，但會犧牲開店現金。", {"copper": -3, "debt": -3}, [
					_line("旁白", "王婆收下銅錢，笑得比進門時更有把握。"),
					_line("潘金蓮", "錢可以再賺，但我總覺得這張單有問題。")
				], {"copper": 3}),
				_choice("delay", "強硬要求延期", "保住現金，但街坊會聽見爭執。", {"reputation": -1, "pan_trust": -1, "ximen_alert": 1}, [
					_line("你", "十日後再算。今日誰敢搬這個爐，我便去縣衙擊鼓。"),
					_line("王婆", "好，我倒要看看十日後你還站不站得住。")
				])
			],
			[
				_line("潘金蓮", "今日總算過咗。你真係同以前唔同。"),
				_line("旁白", "第一日結束。門外有人停留片刻，似乎正在記錄武家今日賣出了多少餅。")
			]
		),
		_day(
			"第一籠之後",
			"找到第一批固定客人",
			[
				_line("旁白", "第二日清晨，昨日買過炊餅的腳夫再次出現，但街角亦多了一個瘦小少年。"),
				_line("潘金蓮", "那個叫鄆哥，清河每條後巷他都熟。也是出了名的小滑頭。"),
				_line("你", "熟路又滑頭，放在對的地方便是人才。")
			],
			[
				_choice("dock_orders", "接碼頭腳夫訂單", "穩定收入，開始建立固定客群。", {"flour": -1, "copper": 7, "reputation": 1}, [
					_line("旁白", "你承諾每天辰時前送到。腳夫們第一次把武家炊餅當成固定早飯。")
				], {"flour": 1}),
				_choice("samples", "派發免費試食", "收入較少，但聲望提升最快。", {"flour": -2, "copper": 2, "reputation": 3}, [
					_line("旁白", "半條街的人都吃到一小塊熱餅。武家的名字開始在巷口傳開。")
				], {"flour": 2}),
				_choice("new_flavour", "試做桂花甜餅", "與潘金蓮合作開發新產品。", {"flour": -1, "copper": 5, "reputation": 2, "pan_trust": 2}, [
					_line("潘金蓮", "桂花不能太多，甜味要留在最後。"),
					_line("你", "第一個新產品，名字就叫金桂餅。")
				], {"flour": 1})
			],
			[
				_line("街坊", "捉賊呀！"),
				_line("旁白", "鄆哥抓起兩個炊餅拔腿便跑，卻在轉角被你截住。他沒有吃，只把其中一個藏進衣服。"),
				_line("鄆哥", "我妹病咗兩日。我會還，真係會還。")
			],
			"你會如何處理偷餅的鄆哥？",
			[
				_choice("recruit_yunge", "讓他以跑腿抵債", "取得街頭情報來源，也給少年一次機會。", {"yunge_loyalty": 3, "intel": 1, "reputation": 1}, [
					_line("你", "兩個餅不值幾文。由今日開始，你替武家跑十趟腿。"),
					_line("鄆哥", "清河邊個收貨、邊個講大話，我都可以替你查。")
				]),
				_choice("follow_yunge", "先跟蹤再決定", "確認他的故事，並發現有人監視武家。", {"yunge_loyalty": 1, "intel": 2}, [
					_line("旁白", "鄆哥真的把餅帶給病中的妹妹。你亦在他家外看見昨日監視武家的灰衣人。")
				]),
				_choice("public_warning", "當街警告後放走", "維持規矩，但失去一部分信任。", {"reputation": 1, "yunge_loyalty": -1}, [
					_line("你", "今日放你一次。下一次偷的可能不只是餅，而是你自己的前路。"),
					_line("鄆哥", "我記住了。")
				])
			],
			[
				_line("旁白", "第二日結束。固定客人帶來穩定收入，而鄆哥亦記住了武家的選擇。")
			]
		),
		_day(
			"王婆的好意",
			"解決麵粉供應",
			[
				_line("旁白", "第三日，原本供貨的糧行突然加價一倍。王婆卻送來一車價格低得不合理的麵粉。"),
				_line("王婆", "大家街坊，我當然要幫你。簽了這張長約，半年都不用怕斷貨。"),
				_line("潘金蓮", "她昨日還要搬我們的爐，今日怎會突然這麼好心？")
			],
			[
				_choice("other_supplier", "尋找城外供應商", "成本較高，但貨源乾淨可靠。", {"copper": -4, "flour": 4, "reputation": 1, "pan_trust": 1}, [
					_line("旁白", "你走了半日找到一戶磨坊。價錢不低，至少每袋都有來源。")
				], {"copper": 4}),
				_choice("test_flour", "買少量樣本檢查", "不急着簽約，先尋找麵粉中的問題。", {"copper": -1, "flour": 1, "intel": 2, "pan_respect": 1}, [
					_line("你", "顏色太白，氣味又苦。這不是普通陳麵。"),
					_line("潘金蓮", "有人想讓我們把問題親手蒸進餅裡。")
				], {"copper": 1}),
				_choice("cheap_stock", "大量買入便宜麵粉", "短期增加庫存，但埋下風險。", {"copper": -2, "flour": 5, "flags": {"accepted_wang_flour": true}}, [
					_line("王婆", "大郎果然識做生意。白紙黑字，以後可不能反悔。"),
					_line("旁白", "潘金蓮沒有再說話，只把其中一袋麵粉單獨放在角落。")
				], {"copper": 2})
			],
			[
				_line("旁白", "黃昏，你發現合約最後一行寫着：若武家名聲受損，所有貨款立即到期，店舖抵押給供貨人。"),
				_line("潘金蓮", "這不是供貨約，是等我們出事的收店契。")
			],
			"王婆正等你在合約上按手印。",
			[
				_choice("reject_contract", "撕掉合約", "公開拒絕陷阱，與潘金蓮站在同一邊。", {"pan_trust": 3, "reputation": 1, "ximen_alert": 1}, [
					_line("你", "想收武家的店，叫背後的人自己來。"),
					_line("王婆", "你會後悔今日這點硬氣。")
				]),
				_choice("fake_accept", "假裝簽約並留下暗記", "讓對方以為計劃成功，換取調查時間。", {"intel": 3, "ximen_alert": -1, "pan_respect": 2, "flags": {"fake_supply_contract": true}}, [
					_line("你", "簽可以，但每頁都要蓋騎縫印。"),
					_line("旁白", "你故意使用一枚缺角手印。任何被替換的頁面都會留下破綻。")
				]),
				_choice("accept_terms", "接受合約換取喘息", "取得更多麵粉，但債務和風險增加。", {"flour": 2, "debt": 4, "pan_trust": -3, "ximen_alert": -1, "flags": {"bound_to_wang_contract": true}}, [
					_line("潘金蓮", "今日是多了幾袋麵，往後每一袋都會變成繩。")
				])
			],
			[
				_line("旁白", "第三日結束。你已知道，武家的危機並不只是一張欠單，而是一場有人安排好的收購。")
			]
		),
		_day(
			"龐春梅入局",
			"守住攤位與帳目",
			[
				_line("旁白", "第四日，一名年輕女子站在武家門前。她叫龐春梅，說自己懂記帳、待客，也懂得如何對付麻煩人。"),
				_line("龐春梅", "我不要賣身契，只要工錢和說話的資格。"),
				_line("潘金蓮", "她是王婆介紹來的。太巧了。")
			],
			[
				_choice("hire_chunmei", "正式聘請龐春梅", "支付工錢，快速提升店舖處理能力。", {"copper": -2, "chunmei_leverage": 3, "pan_respect": 1}, [
					_line("龐春梅", "既然叫我做事，帳和客都交給我。做得不好，我自己走。")
				], {"copper": 2}),
				_choice("trial_shift", "安排一日試工", "保留戒心，同時觀察她的能力。", {"copper": -1, "chunmei_leverage": 2, "intel": 1}, [
					_line("旁白", "半日之內，春梅找出三筆漏收的貨款，也記住所有來問價卻不買的陌生人。")
				], {"copper": 1}),
				_choice("keep_distance", "拒絕聘請並暗中觀察", "不增加成本，取得她與王婆聯絡的線索。", {"intel": 2, "chunmei_leverage": -1}, [
					_line("旁白", "春梅離開後沒有回王婆茶坊，反而把一張紙條塞進城牆裂縫。")
				])
			],
			[
				_line("旁白", "黃昏，三名醉漢堵住攤位，聲稱武家的餅又硬又貴。他們說話時卻不斷看向街對面的灰衣人。"),
				_line("醉漢", "除非今日免費送全條街，否則別想繼續做生意！")
			],
			"這不是普通客訴。你準備如何拆局？",
			[
				_choice("chunmei_handles", "讓龐春梅反問證詞", "利用她的觀察力，當眾拆穿假客人。", {"reputation": 3, "chunmei_leverage": 2, "intel": 1}, [
					_line("龐春梅", "你說昨日買過，卻連攤位朝哪邊都答不出。誰給你們錢？"),
					_line("旁白", "圍觀街坊大笑，三人狼狽離開。")
				], {"chunmei_leverage": 2}),
				_choice("compensate_crowd", "派餅安撫街坊", "花錢平息衝突，保持店舖營業。", {"copper": -2, "flour": -1, "reputation": 2}, [
					_line("你", "真假由大家吃過再判。今日每戶分半個，明日再來付錢。")
				], {"copper": 2, "flour": 1}),
				_choice("record_instigator", "不爭辯，跟蹤灰衣人", "暫時承受議論，換取幕後線索。", {"reputation": -1, "intel": 3, "ximen_alert": 1}, [
					_line("旁白", "灰衣人最後從西門府側門進去。第一次，幕後人的輪廓變得清楚。")
				])
			],
			[
				_line("龐春梅", "你可以當我是夥計，也可以當我是棋子。但最好記住，棋子也會自己揀方向。"),
				_line("旁白", "第四日結束。武家開始不再只靠大郎一雙手。")
			]
		),
		_day(
			"毒餅風波",
			"在封店前找出證據",
			[
				_line("旁白", "第五日午前，三名街坊吃過炊餅後腹痛倒地。官差封住攤位，圍觀者開始高喊毒餅。"),
				_line("官差", "日落前交不出解釋，武家停業，所有麵粉送官檢驗。"),
				_line("潘金蓮", "他們不是想害幾個客人，是想一次毀掉我們的名字。")
			],
			[
				_choice("inspect_batch", "檢查麵粉和蒸籠", "從原料差異尋找下毒方式。", {"intel": 3, "pan_respect": 1}, [
					_line("你", "只有靠門邊一籠有苦味。毒不在麵粉，是出爐後才被灑上去。")
				]),
				_choice("visit_patients", "帶大夫探望病人", "花費銅錢，但保住街坊信任並取得症狀證詞。", {"copper": -3, "reputation": 2, "intel": 2, "pan_trust": 1}, [
					_line("大夫", "只是巴豆，不會致命。有人刻意製造混亂，不是要殺人。")
				], {"copper": 3}),
				_choice("ask_yunge", "讓鄆哥追查送貨人", "最快取得目擊證據。", {"intel": 4, "yunge_loyalty": 1}, [
					_line("鄆哥", "我見到那灰衣人扮成客人，手一直放在袖口。他去了王婆後門。")
				], {"yunge_loyalty": 2})
			],
			[
				_line("官差", "時辰到了。武大，你有證據便說，沒有便跟我回衙門。"),
				_line("王婆", "大家都看見人是吃了武家的餅才倒下。還有什麼好查？")
			],
			"你必須在街坊面前決定如何回應毒餅指控。",
			[
				_choice("present_chain", "展示完整證據鏈", "以原料、症狀和目擊證詞反證下毒。", {"reputation": 5, "debt": -3, "ximen_alert": 3}, [
					_line("你", "毒只在一籠、出爐後才出現，灰衣人又由王婆後門離開。這不是失手，是栽贓。"),
					_line("官差", "證物先封存。武家可以暫時復業。")
				], {"intel": 7}),
				_choice("compensate_victims", "先賠償並承諾查明", "承擔責任換取復業，但成本沉重。", {"copper": -5, "reputation": 2, "pan_trust": 2, "debt": 1}, [
					_line("你", "不論毒從哪裡來，餅由武家交出去，我先負責。"),
					_line("街坊", "至少大郎沒有逃。讓他查下去。")
				], {"copper": 5}),
				_choice("accuse_wang", "直接指控王婆", "證據不足也要正面開戰。", {"reputation": -2, "intel": 1, "ximen_alert": 2}, [
					_line("王婆", "空口指人下毒？大家聽清楚，是他自己心虛。"),
					_line("旁白", "衝突沒有結束，只是被推遲到下一次。")
				])
			],
			[
				_line("潘金蓮", "今日之後，所有原料、出爐和交貨都要有人簽名。"),
				_line("你", "好。武家不只要會做餅，還要建立別人破壞不了的規矩。")
			]
		),
		_day(
			"李瓶兒的帳",
			"取得西門家的帳目線索",
			[
				_line("旁白", "第六日，一頂沒有標記的轎停在後巷。轎中人是李瓶兒，她知道西門慶正在收購清河的糧店。"),
				_line("李瓶兒", "西門家的帳有一本在我手上，也有一本失了。你替我找回失帳，我給你證明欠單來源的頁面。"),
				_line("潘金蓮", "她不是來救我們。她只是想看看我們值不值得合作。")
			],
			[
				_choice("joint_meeting", "邀潘金蓮共同談判", "透明合作，平衡兩段關係。", {"li_interest": 2, "pan_trust": 3, "pan_respect": 2, "intel": 1}, [
					_line("潘金蓮", "條件由三個人一起講清楚，日後便沒有人可以拿秘密作價。"),
					_line("李瓶兒", "武家真正難對付的，原來不是只有大郎。")
				]),
				_choice("private_bargain", "私下與李瓶兒交易", "取得較強支持，但傷害潘金蓮信任。", {"li_interest": 4, "pan_trust": -3, "intel": 2}, [
					_line("李瓶兒", "你願意冒險，我便多給你一個名字：西門府管帳人來旺。")
				]),
				_choice("follow_money", "先追查失帳去向", "不用承諾站隊，集中累積情報。", {"copper": -1, "intel": 4, "li_interest": 1}, [
					_line("旁白", "你從當鋪找到被撕下的帳角，上面記着王婆收過三筆『清路費』。")
				], {"copper": 1})
			],
			[
				_line("李瓶兒", "帳找到了。現在輪到你決定，證據應該放在誰手上。"),
				_line("旁白", "原帳足以威脅西門慶，也足以把李瓶兒捲入風暴。")
			],
			"如何使用李瓶兒交出的帳頁？",
			[
				_choice("copy_and_return", "抄錄後歸還原帳", "保護李瓶兒，同時保留可驗證的線索。", {"li_interest": 3, "intel": 3, "ximen_alert": 1}, [
					_line("李瓶兒", "懂得留下證據，也懂得不把盟友逼上絕路。這宗生意可以繼續。")
				]),
				_choice("hold_original", "扣下原帳作籌碼", "掌握最強證物，但令各方提高警戒。", {"li_interest": -2, "intel": 5, "ximen_alert": 3, "flags": {"holding_ximen_ledger": true}}, [
					_line("李瓶兒", "拿得住這本帳，才叫籌碼。拿不住，便是催命符。")
				]),
				_choice("trade_debt_page", "只換取欠單證明", "立即削弱債務風險，不深涉其他秘密。", {"debt": -6, "li_interest": 1, "intel": 2}, [
					_line("旁白", "帳頁顯示，武家的欠款已被西門府買下，而且金額被人加了兩次。")
				])
			],
			[
				_line("旁白", "第六日結束。武家第一次擁有可以反過來威脅西門慶的東西。")
			]
		),
		_day(
			"共同掌櫃",
			"決定武家的權力與方向",
			[
				_line("潘金蓮", "產品、包裝、客人說什麼，都是我在記。但所有人仍只當我是武大的妻。"),
				_line("旁白", "第七日清晨，她把重新整理的帳本放到桌上。數字比你記的更完整，連每位熟客的口味也在其中。"),
				_line("潘金蓮", "如果這間店要翻身，我要知道自己到底是什麼身份。")
			],
			[
				_choice("equal_partner", "邀她成為共同掌櫃", "分享決策、利潤與風險。", {"pan_trust": 5, "pan_respect": 4, "reputation": 1, "flags": {"pan_chapter1_role": "equal_partner"}}, [
					_line("你", "由今日開始，武家的帳有兩個掌櫃簽名。"),
					_line("潘金蓮", "那我也會以掌櫃身份，為每一個決定負責。")
				]),
				_choice("brand_lead", "讓她主理產品與品牌", "給予獨立權力，發揮她最強的才能。", {"pan_trust": 4, "pan_respect": 5, "reputation": 2, "flags": {"pan_chapter1_role": "brand_lead"}}, [
					_line("潘金蓮", "七日內，我會讓清河人看見紅紙武字，就想起我們的餅。")
				]),
				_choice("traditional_role", "要求她留在後房", "短期避免外界議論，嚴重傷害關係。", {"pan_trust": -5, "pan_respect": -4, "reputation": 1, "flags": {"pan_chapter1_role": "restricted"}}, [
					_line("潘金蓮", "我明白了。你想改自己的命，卻不打算讓我改。")
				])
			],
			[
				_line("龐春梅", "我在欠單和西門府帳頁上找到同一個缺口印。偽造欠單的人今晚會去王婆茶坊換印。"),
				_line("旁白", "這是公開揭穿欠單的機會，也可能是西門慶故意放出的餌。")
			],
			"你會如何處理偽造欠單的印章？",
			[
				_choice("compare_seals", "暗中取得印樣比對", "穩妥累積證據，不立即驚動對方。", {"intel": 3, "pan_respect": 1}, [
					_line("旁白", "兩個缺口完全吻合。偽造欠單與西門府帳房已經連成一線。")
				]),
				_choice("trap_wang", "設局讓王婆親口承認", "削弱債務，但令西門慶提高警戒。", {"debt": -5, "intel": 2, "ximen_alert": 3, "chunmei_leverage": 1}, [
					_line("王婆", "我只是替人換張紙——"),
					_line("龐春梅", "夠了。這一句已有人在門外聽見。")
				], {"chunmei_leverage": 2}),
				_choice("public_charge", "帶證據到街上公開", "利用已有情報發動輿論反擊。", {"reputation": 4, "debt": -4, "ximen_alert": 4}, [
					_line("你", "欠單、帳頁和印章都在這裡。明日我便把副本送到縣衙。"),
					_line("旁白", "西門府第一次連夜關上側門。")
				], {"intel": 10})
			],
			[
				_line("旁白", "第七日結束。武家不只確立了店舖方向，也開始決定誰有權改寫這個家的命。")
			]
		),
		_day(
			"武松歸來",
			"取得武松信任",
			[
				_line("旁白", "第八日，一名高大漢子推門入屋。行李未放，目光已掃過新帳、僱員和門外監視的人。"),
				_line("武松", "兄長，我離開不久，武家為何欠了西門府的錢，還與這麼多人結怨？"),
				_line("潘金蓮", "他不是來替我們打架。他要先知道，眼前的兄長值不值得相信。")
			],
			[
				_choice("show_books", "公開十日內所有帳目", "以透明經營證明自己沒有欺騙家人。", {"wu_trust": 3, "pan_respect": 1, "intel": 1}, [
					_line("武松", "每一文來去都有記。兄長做的不是賭局，是生意。")
				]),
				_choice("feed_neighbours", "請武松看街坊如何回應", "用實際聲望證明武家的改變。", {"copper": -3, "reputation": 3, "wu_trust": 2}, [
					_line("街坊", "武家出事後沒有逃，還親自帶大夫看病。"),
					_line("武松", "人言未必可信，但十個人都這樣說，便值得聽。")
				], {"copper": 3}),
				_choice("ask_force", "直接請武松保護店舖", "得到暫時威懾，但令他懷疑你的動機。", {"wu_trust": -1, "ximen_alert": 2}, [
					_line("武松", "若有人行兇，我自然會管。但兄長若只想借我的拳頭做生意，我不會答應。")
				])
			],
			[
				_line("武松", "我只問一次。這張欠單、毒餅和西門家的帳，到底有多少是你親眼查到，多少只是猜？"),
				_line("旁白", "武松要的不是漂亮答案，而是你是否願意承認風險和錯誤。")
			],
			"你會如何向武松解釋這八日發生的事？",
			[
				_choice("full_truth", "如實說出所有選擇與失誤", "坦白能建立最穩定的兄弟信任。", {"wu_trust": 4, "pan_trust": 1}, [
					_line("武松", "兄長肯認錯，也肯負責。我不替你做生意，但誰用刀逼武家，我會站在門前。")
				]),
				_choice("show_evidence", "只讓證據說話", "情報充分時，以完整證據取得認可。", {"wu_trust": 4, "reputation": 1}, [
					_line("武松", "證據比傳聞硬。明日若要上公堂，我替你把這些送到知縣面前。")
				], {"intel": 10}),
				_choice("appeal_family", "以兄弟情義要求支持", "取得有限支持，但沒有消除他的疑問。", {"wu_trust": 1, "pan_trust": 1}, [
					_line("武松", "你是我兄長，我不會看你送命。但有些事，我仍要自己查。")
				])
			],
			[
				_line("旁白", "第八日結束。武松是否站到武家一邊，取決於你累積的不是金錢，而是可信的行動。")
			]
		),
		_day(
			"西門夜宴",
			"拒絕西門慶的收購",
			[
				_line("旁白", "第九日，西門府送來請柬。清河糧商、酒樓掌櫃與燈會管事全在受邀之列。"),
				_line("西門慶", "武家最近很有意思。我願出五十貫買下招牌、配方和燈會攤位。大郎可以安穩過下半世。"),
				_line("你", "這不是買賣。你是想在燈會前讓武家消失。")
			],
			[
				_choice("merchant_alliance", "聯絡受壓商戶", "付出資金建立共同談判陣線。", {"copper": -3, "reputation": 3, "intel": 1}, [
					_line("旁白", "三家小店答應在宴上一起拒絕不公平供貨條件。武家不再孤立。")
				], {"copper": 3}),
				_choice("rehearse_case", "與潘金蓮整理談判次序", "增加情報和臨場判斷。", {"intel": 3, "pan_respect": 2}, [
					_line("潘金蓮", "先談偽造欠單，再談毒餅，最後才放出帳頁。不要一開始便亮出所有牌。")
				]),
				_choice("false_information", "讓龐春梅放出假消息", "令西門慶誤判武家的證據位置。", {"intel": 2, "ximen_alert": -2, "chunmei_leverage": 2, "flags": {"ximen_misdirected": true}}, [
					_line("龐春梅", "今夜他的人會去碼頭找一本根本不存在的原帳。我們有半晚時間。")
				], {"chunmei_leverage": 3})
			],
			[
				_line("西門慶", "五十貫不要，那我便讓你十日後連五文都拿不到。"),
				_line("旁白", "宴廳安靜下來。所有掌櫃都在等，看武大郎會低頭、翻桌，還是提出另一個價。")
			],
			"西門慶要求你當場交出武家招牌。",
			[
				_choice("business_counter", "提出公開公平供貨契約", "把私人威脅變成所有商戶共同面對的條款。", {"reputation": 4, "copper": 3, "ximen_alert": 3}, [
					_line("你", "你真想做生意，就在所有掌櫃面前簽同價供貨。若不敢，便證明你只想壟斷。"),
					_line("旁白", "幾名掌櫃第一次抬頭附和武家。")
				]),
				_choice("expose_ledger", "公開西門府帳目", "情報充分時發動最猛烈反擊。", {"reputation": 6, "debt": -7, "ximen_alert": 5}, [
					_line("你", "這裡記着糧價、清路費和武家假欠單。明日每一頁都會出現在燈會。"),
					_line("西門慶", "很好。那就看你能不能活着把攤開起來。")
				], {"intel": 13}),
				_choice("feign_surrender", "假意接受收購", "降低即時警戒，為燈會設下反制。", {"intel": 3, "reputation": -1, "ximen_alert": -3, "flags": {"feigned_surrender": true}}, [
					_line("你", "合約明日在燈會攤位交。我要當着管事的面簽。"),
					_line("旁白", "西門慶以為你低頭，卻不知道潘金蓮已將真正證據分成三份。")
				])
			],
			[
				_line("潘金蓮", "明日不是賣得多就算贏。要讓全清河看見，武家可以在西門府面前開門做生意。"),
				_line("旁白", "第九日結束。上元燈會將決定第一章所有選擇的價值。")
			]
		),
		_day(
			"上元燈會",
			"守住攤位，完成十日逆命",
			[
				_line("旁白", "第十日，上元燈會。武家攤位前掛起紅字招牌，街坊、商戶、官差和西門府的人同時到場。"),
				_line("潘金蓮", "爐、餅、帳和證據都準備好。今日每一個來買餅的人，也是在看武家能不能站住。"),
				_line("你", "開爐。十日前我們只有十七文，今日要把第一條命路真正打開。")
			],
			[
				_choice("premium_stall", "推出限量金桂燈會餅", "高成本、高收入，以產品建立品牌。", {"flour": -3, "copper": 12, "reputation": 3, "pan_trust": 2}, [
					_line("旁白", "金桂香氣沿燈街散開。未到午時，武家攤前已經排起長隊。")
				], {"flour": 3}),
				_choice("community_price", "維持街坊平價", "少賺一點，換取最多民眾支持。", {"flour": -2, "copper": 7, "reputation": 5}, [
					_line("街坊", "別家都趁燈會加價，武家沒有。今日我們就守在這裡買。")
				], {"flour": 2}),
				_choice("evidence_stall", "把攤位變成公開證據台", "減少生產，準備章末揭露。", {"flour": -1, "copper": 3, "intel": 3, "reputation": 2, "ximen_alert": 2}, [
					_line("旁白", "每個餅袋都印着欠單時間線。人們一邊吃，一邊讀懂西門府如何逼收小店。")
				], {"flour": 1}),
				_choice("emergency_stock", "借入緊急麵粉開攤", "即使資源不足也能完成燈會，但增加債務。", {"flour": 1, "debt": 3, "copper": 4, "reputation": 1}, [
					_line("你", "今日先讓爐火不停。這筆急債，之後再用生意還。")
				])
			],
			[
				_line("旁白", "入夜前，攤位後方突然起火。兩名蒙面人同時搶走帳箱，西門府管事則帶着收購合約逼近。"),
				_line("西門慶", "武大郎，火一燒、帳一失，你還有什麼？"),
				_line("潘金蓮", "我們還有十日內每一個被你低估的人。")
			],
			"最後一次選擇：你用什麼守住武家的命？",
			[
				_choice("people_line", "號召街坊救火守攤", "以十日累積的聲望對抗破壞。", {"reputation": 5, "pan_trust": 2, "debt": -3}, [
					_line("你", "先救旁邊攤位，再救帳！所有水桶由左邊傳入！"),
					_line("旁白", "腳夫、街坊和小掌櫃排成長線。火沒有吞掉武家的招牌。")
				]),
				_choice("wusong_guard", "讓武松截住搶帳者", "兄弟信任足夠時，保住原始證物。", {"wu_trust": 2, "reputation": 4, "debt": -5, "ximen_alert": 3}, [
					_line("武松", "救火歸大家，這兩個人交給我。"),
					_line("旁白", "蒙面人未走出十步便被按在燈架下，袖中仍藏着西門府腰牌。")
				], {"wu_trust": 5}),
				_choice("public_evidence", "公開全部帳目與證人", "情報充分時，一次擊破欠單和毒餅陰謀。", {"reputation": 7, "debt": -10, "ximen_alert": 5}, [
					_line("你", "帳有三份，證人有五個。燒一個攤，燒不掉整條街知道的真相。"),
					_line("官差", "西門府管事、王婆及縱火者，全部帶回縣衙。")
				], {"intel": 16}),
				_choice("save_family", "先帶所有人安全離開", "放棄部分貨物，但不以任何人的命換勝利。", {"copper": -4, "reputation": 3, "pan_trust": 4, "debt": 1}, [
					_line("你", "貨可以再做，人不能。全部離開火場，一個都不要少。"),
					_line("潘金蓮", "招牌燒了可以重寫。只要掌櫃還在，武家就沒有輸。")
				])
			],
			[
				_line("旁白", "燈火再次亮起時，武家仍在。有人記住炊餅的味道，有人記住帳頁上的名字，也有人第一次叫你武掌櫃。"),
				_line("潘金蓮", "第一桶金未必很多。但由今日開始，我們有資格決定下一盤生意怎樣做。"),
				_line("你", "下一次不只是一籠餅。我要開一口全清河都未見過的鍋。")
			]
		)
	]
