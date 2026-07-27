class_name PrologueMusicDirector
extends Node

const TRACK_PATHS := {
	"modern": "res://assets/audio/prologue/s1.mp3",
	"song": "res://assets/audio/prologue/s2.mp3"
}
const TRACK_VOLUMES := {
	"modern": -14.0,
	"song": -13.0
}

var channels: Array[AudioStreamPlayer] = []
var active_channel := -1
var active_track := ""
var fade_tween: Tween
var duck_tween: Tween

func _ready() -> void:
	if OS.has_feature("web"):
		_web_call("unlock")
		return
	for index in 2:
		var player := AudioStreamPlayer.new()
		player.name = "StoryMusic%02d" % index
		player.bus = "Master"
		player.volume_db = -60.0
		player.playback_type = AudioServer.PLAYBACK_TYPE_STREAM
		add_child(player)
		channels.append(player)

func play_track(id: String, fade_seconds := 1.5) -> void:
	if not TRACK_PATHS.has(id) or id == active_track:
		return
	if OS.has_feature("web"):
		_web_call("playTrack", [id, fade_seconds])
		active_track = id
		return
	var incoming_index := 0 if active_channel != 0 else 1
	var incoming := channels[incoming_index]
	var track := load(TRACK_PATHS[id]) as AudioStreamMP3
	if track == null:
		push_warning("Unable to load prologue music: " + str(TRACK_PATHS[id]))
		return
	track.loop = true
	incoming.stream = track
	incoming.volume_db = -60.0
	incoming.play()
	if fade_tween and fade_tween.is_valid():
		fade_tween.kill()
	if duck_tween and duck_tween.is_valid():
		duck_tween.kill()
	var outgoing: AudioStreamPlayer = channels[active_channel] if active_channel >= 0 else null
	fade_tween = create_tween().set_parallel(true)
	fade_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	fade_tween.tween_property(incoming, "volume_db", float(TRACK_VOLUMES[id]), fade_seconds)
	if outgoing != null and outgoing.playing:
		fade_tween.tween_property(outgoing, "volume_db", -60.0, fade_seconds)
		fade_tween.chain().tween_callback(func() -> void: outgoing.stop())
	active_channel = incoming_index
	active_track = id

func duck(amount_db := 8.0, hold_seconds := 1.6) -> void:
	if OS.has_feature("web"):
		_web_call("duck", [amount_db, hold_seconds])
		return
	if active_channel < 0:
		return
	var player := channels[active_channel]
	var base_volume := float(TRACK_VOLUMES.get(active_track, -14.0))
	if duck_tween and duck_tween.is_valid():
		duck_tween.kill()
	duck_tween = create_tween()
	duck_tween.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_OUT)
	duck_tween.tween_property(player, "volume_db", base_volume - amount_db, 0.16)
	duck_tween.tween_interval(hold_seconds)
	duck_tween.tween_property(player, "volume_db", base_volume, 0.42)

func stop_all(fade_seconds := 0.5) -> void:
	if OS.has_feature("web"):
		_web_call("stopAll", [fade_seconds])
		active_track = ""
		return
	if channels.is_empty():
		return
	if fade_tween and fade_tween.is_valid():
		fade_tween.kill()
	fade_tween = create_tween().set_parallel(true)
	for player in channels:
		if player.playing:
			fade_tween.tween_property(player, "volume_db", -60.0, fade_seconds)
	fade_tween.chain().tween_callback(func() -> void:
		for player in channels:
			player.stop()
	)
	active_track = ""
	active_channel = -1

func _exit_tree() -> void:
	if OS.has_feature("web"):
		_web_call("stopAll", [0.08])
		return
	for player in channels:
		player.stop()

func _web_call(method: String, values: Array = []) -> void:
	var encoded := PackedStringArray()
	for value in values:
		encoded.append(JSON.stringify(value))
	JavaScriptBridge.eval("""
		(() => {
			const director = window.nimingStoryMusic;
			if (director && typeof director.%s === 'function') director.%s(%s);
		})()
	""" % [method, method, ",".join(encoded)])
