class_name WuxiaOST
extends AudioStreamPlayer

const TRACK_PATH := "res://assets/audio/guzheng-theme.mp3"
const WEB_AUDIO_ID := "niming-ost"

func _ready() -> void:
	if OS.has_feature("web"):
		_try_resume_web_audio()
		return
	var track := load(TRACK_PATH) as AudioStreamMP3
	if track == null:
		push_warning("Unable to load soundtrack: " + TRACK_PATH)
		return
	track.loop = true
	stream = track
	playback_type = AudioServer.PLAYBACK_TYPE_STREAM
	volume_db = -13.0
	play()

func toggle_music() -> void:
	if OS.has_feature("web"):
		JavaScriptBridge.eval("""
			(() => {
				const audio = document.getElementById('%s');
				if (!audio) return;
				if (audio.paused) {
					audio.play().catch(() => {});
				} else {
					audio.pause();
				}
			})()
		""" % WEB_AUDIO_ID)
		return
	stream_paused = not stream_paused

func is_music_paused() -> bool:
	if OS.has_feature("web"):
		return bool(JavaScriptBridge.eval("""
			(() => {
				const audio = document.getElementById('%s');
				return !audio || audio.paused;
			})()
		""" % WEB_AUDIO_ID))
	return stream_paused

static func stop_web_audio() -> void:
	if not OS.has_feature("web"):
		return
	JavaScriptBridge.eval("""
		(() => {
			const audio = document.getElementById('%s');
			if (audio) audio.pause();
		})()
	""" % WEB_AUDIO_ID)

func _try_resume_web_audio() -> void:
	JavaScriptBridge.eval("""
		(() => {
			const audio = document.getElementById('%s');
			if (audio) audio.play().catch(() => {});
		})()
	""" % WEB_AUDIO_ID)
