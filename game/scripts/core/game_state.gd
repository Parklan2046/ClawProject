extends Node

const ORIGINS := {
	"chef": {
		"name": "餐飲廚師",
		"talent": "火候直覺",
		"description": "烹飪判定更寬鬆，成品質量提高。"
	},
	"brand": {
		"name": "品牌策劃",
		"talent": "人心定價",
		"description": "品牌與口碑事件獲得額外聲望。"
	},
	"logistics": {
		"name": "外賣營運",
		"talent": "街巷成網",
		"description": "配送速度提高，可同時處理更多訂單。"
	},
	"finance": {
		"name": "財務管理",
		"talent": "分文必算",
		"description": "材料成本與借貸利息降低。"
	}
}

const PRINCIPLES := {
	"benevolent": "仁義",
	"pragmatic": "務實",
	"bold": "冒險",
	"cunning": "權謀"
}

var player_name := "無名"
var origin_id := ""
var principle_id := ""
var copper := 17
var flour := 3
var debt := 30
var intel := 0
var ximen_alert := 0
var reputation := 0
var relationship := {
	"pan_trust": 0,
	"pan_respect": 0,
	"li_interest": 0,
	"chunmei_leverage": 0,
	"yunge_loyalty": 0,
	"wu_trust": 0
}
var flags: Dictionary = {}
var chapter := 0
var chapter_day := 0
var checkpoint := "prologue_start"

func reset_prologue() -> void:
	origin_id = ""
	principle_id = ""
	copper = 17
	flour = 3
	debt = 30
	intel = 0
	ximen_alert = 0
	reputation = 0
	relationship = {
		"pan_trust": 0,
		"pan_respect": 0,
		"li_interest": 0,
		"chunmei_leverage": 0,
		"yunge_loyalty": 0,
		"wu_trust": 0
	}
	flags = {}
	chapter = 0
	chapter_day = 0
	checkpoint = "prologue_start"

func begin_chapter_one() -> void:
	chapter = 1
	chapter_day = 1
	flour = 3
	debt = 30
	intel = 0
	ximen_alert = 0
	checkpoint = "chapter_01_day_01"
	set_flag("chapter_01_complete", false)

func origin_name() -> String:
	return ORIGINS.get(origin_id, {}).get("name", "尚未選擇")

func principle_name() -> String:
	return PRINCIPLES.get(principle_id, "尚未選擇")

func set_flag(key: String, value: Variant = true) -> void:
	flags[key] = value

func get_flag(key: String, fallback: Variant = false) -> Variant:
	return flags.get(key, fallback)

func serialize() -> Dictionary:
	return {
		"version": 1,
		"player_name": player_name,
		"origin_id": origin_id,
		"principle_id": principle_id,
		"copper": copper,
		"flour": flour,
		"debt": debt,
		"intel": intel,
		"ximen_alert": ximen_alert,
		"reputation": reputation,
		"relationship": relationship.duplicate(true),
		"flags": flags.duplicate(true),
		"chapter": chapter,
		"chapter_day": chapter_day,
		"checkpoint": checkpoint
	}

func restore(data: Dictionary) -> void:
	player_name = str(data.get("player_name", "無名"))
	origin_id = str(data.get("origin_id", ""))
	principle_id = str(data.get("principle_id", ""))
	copper = int(data.get("copper", 17))
	flour = int(data.get("flour", 3))
	debt = int(data.get("debt", 30))
	intel = int(data.get("intel", 0))
	ximen_alert = int(data.get("ximen_alert", 0))
	reputation = int(data.get("reputation", 0))
	relationship = data.get("relationship", relationship).duplicate(true)
	for key in ["pan_trust", "pan_respect", "li_interest", "chunmei_leverage", "yunge_loyalty", "wu_trust"]:
		if not relationship.has(key):
			relationship[key] = 0
	flags = data.get("flags", {}).duplicate(true)
	chapter = int(data.get("chapter", 0))
	chapter_day = int(data.get("chapter_day", 0))
	checkpoint = str(data.get("checkpoint", "prologue_start"))
