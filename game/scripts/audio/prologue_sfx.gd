class_name PrologueSFX
extends Node

const SAMPLE_RATE := 22050
const PLAYER_COUNT := 8
const AMBIENCE_VOLUMES := {
	"modern": -26.0,
	"song_home": -28.0
}

var players: Array[AudioStreamPlayer] = []
var ambience_player: AudioStreamPlayer
var streams: Dictionary = {}
var ambience_streams: Dictionary = {}
var next_player := 0

func _ready() -> void:
	if OS.has_feature("web"):
		_web_call("unlock")
		return
	for index in PLAYER_COUNT:
		var player := AudioStreamPlayer.new()
		player.name = "SFXVoice%02d" % index
		player.bus = "Master"
		add_child(player)
		players.append(player)
	ambience_player = AudioStreamPlayer.new()
	ambience_player.name = "PrologueAmbience"
	ambience_player.bus = "Master"
	ambience_player.volume_db = -28.0
	add_child(ambience_player)
	_build_native_streams()

func play(cue: String) -> void:
	if cue.is_empty():
		return
	if OS.has_feature("web"):
		_web_call("play", cue)
		return
	var stream: AudioStreamWAV = streams.get(cue)
	if stream == null or players.is_empty():
		return
	var player := _available_player()
	player.stream = stream
	player.volume_db = _native_volume(cue)
	player.pitch_scale = 1.0
	player.play()

func start_ambience(id: String) -> void:
	if OS.has_feature("web"):
		_web_call("startAmbience", id)
		return
	var stream: AudioStreamWAV = ambience_streams.get(id)
	if stream == null:
		return
	ambience_player.stream = stream
	ambience_player.volume_db = float(AMBIENCE_VOLUMES.get(id, -28.0))
	ambience_player.play()

func stop_ambience(fade_seconds := 0.35) -> void:
	if OS.has_feature("web"):
		_web_call("stopAmbience", fade_seconds)
		return
	if ambience_player == null or not ambience_player.playing:
		return
	if fade_seconds <= 0.01:
		ambience_player.stop()
		return
	var tween := create_tween()
	tween.tween_property(ambience_player, "volume_db", -46.0, fade_seconds)
	tween.tween_callback(func() -> void:
		ambience_player.stop()
		ambience_player.volume_db = -28.0
	)

func stop_all() -> void:
	if OS.has_feature("web"):
		_web_call("stopAll")
		return
	for player in players:
		player.stop()
	if ambience_player != null:
		ambience_player.stop()

func _exit_tree() -> void:
	stop_all()

func _available_player() -> AudioStreamPlayer:
	for player in players:
		if not player.playing:
			return player
	var player := players[next_player]
	next_player = (next_player + 1) % players.size()
	return player

func _web_call(method: String, value: Variant = null) -> void:
	var argument := ""
	if value != null:
		argument = JSON.stringify(value)
	JavaScriptBridge.eval("""
		(() => {
			const engine = window.nimingSFX;
			if (engine && typeof engine.%s === 'function') engine.%s(%s);
		})()
	""" % [method, method, argument])

func _build_native_streams() -> void:
	streams = {
		"notification": _tone(0.24, 920.0, 1360.0, 0.22, "sine", 12.0),
		"paper": _noise(0.24, 0.18, 0.62, 720.0),
		"voicemail": _tone(0.42, 148.0, 132.0, 0.20, "square", 18.0),
		"rain_focus": _noise(0.42, 0.09, 0.36, 1400.0),
		"choice": _tone(0.20, 480.0, 720.0, 0.27, "triangle", 10.0),
		"transition": _noise_tone(1.35, 0.20, 92.0, 42.0),
		"wake": _noise_tone(0.48, 0.22, 118.0, 76.0),
		"memory": _tone(0.72, 310.0, 188.0, 0.13, "sine", 5.0),
		"coins": _tone(0.34, 1820.0, 1160.0, 0.20, "triangle", 18.0),
		"steamer": _noise_tone(0.38, 0.20, 620.0, 410.0),
		"debt": _noise(0.32, 0.18, 0.58, 640.0),
		"stove": _noise_tone(0.38, 0.25, 104.0, 72.0),
		"pan_enter": _tone(0.46, 390.0, 590.0, 0.14, "sine", 7.0),
		"contract_equal": _tone(0.42, 440.0, 880.0, 0.29, "triangle", 7.0),
		"contract_trial": _tone(0.34, 390.0, 560.0, 0.25, "triangle", 9.0),
		"contract_refuse": _tone(0.44, 220.0, 128.0, 0.28, "triangle", 8.0),
		"repair_prepare": _noise_tone(0.44, 0.18, 124.0, 96.0),
		"gauge_start": _tone(0.12, 520.0, 520.0, 0.12, "triangle", 16.0),
		"gauge_perfect": _tone(0.28, 740.0, 1320.0, 0.22, "sine", 10.0),
		"gauge_good": _tone(0.22, 470.0, 680.0, 0.18, "triangle", 12.0),
		"gauge_miss": _noise_tone(0.30, 0.20, 130.0, 78.0),
		"fire_master": _noise_tone(1.05, 0.27, 170.0, 320.0),
		"fire_steady": _noise_tone(0.78, 0.23, 140.0, 230.0),
		"fire_fragile": _noise_tone(0.62, 0.18, 110.0, 82.0),
		"summary": _tone(0.78, 330.0, 990.0, 0.20, "sine", 5.0)
	}
	ambience_streams = {
		"modern": _ambience(4.0, 0.17, 58.0, 0.018, 0.72),
		"song_home": _ambience(4.0, 0.10, 86.0, 0.012, 0.36)
	}

func _tone(duration: float, start_hz: float, end_hz: float, gain: float, wave: String, decay: float) -> AudioStreamWAV:
	var count := maxi(1, int(duration * SAMPLE_RATE))
	var samples := PackedFloat32Array()
	samples.resize(count)
	var phase := 0.0
	for index in count:
		var progress := float(index) / float(maxi(1, count - 1))
		var frequency := lerpf(start_hz, end_hz, progress)
		phase += TAU * frequency / float(SAMPLE_RATE)
		var shape := sin(phase)
		if wave == "triangle":
			shape = asin(sin(phase)) * 2.0 / PI
		elif wave == "square":
			shape = 1.0 if sin(phase) >= 0.0 else -1.0
		var envelope := pow(1.0 - progress, maxf(0.8, decay * 0.12))
		samples[index] = shape * gain * envelope
	return _wav_from_samples(samples)

func _noise(duration: float, gain: float, smoothing: float, color_hz: float) -> AudioStreamWAV:
	var count := maxi(1, int(duration * SAMPLE_RATE))
	var samples := PackedFloat32Array()
	samples.resize(count)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(duration * 100000.0 + color_hz)
	var state := 0.0
	var blend := clampf(color_hz / float(SAMPLE_RATE), 0.008, 0.42)
	for index in count:
		var progress := float(index) / float(maxi(1, count - 1))
		state = lerpf(state, rng.randf_range(-1.0, 1.0), blend)
		var envelope := sin(PI * progress) * pow(1.0 - progress, smoothing)
		samples[index] = state * gain * envelope
	return _wav_from_samples(samples)

func _noise_tone(duration: float, gain: float, start_hz: float, end_hz: float) -> AudioStreamWAV:
	var count := maxi(1, int(duration * SAMPLE_RATE))
	var samples := PackedFloat32Array()
	samples.resize(count)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(duration * 73001.0 + start_hz * 31.0)
	var phase := 0.0
	var noise_state := 0.0
	for index in count:
		var progress := float(index) / float(maxi(1, count - 1))
		phase += TAU * lerpf(start_hz, end_hz, progress) / float(SAMPLE_RATE)
		noise_state = lerpf(noise_state, rng.randf_range(-1.0, 1.0), 0.12)
		var envelope := sin(PI * clampf(progress * 1.4, 0.0, 1.0)) * pow(1.0 - progress, 0.7)
		samples[index] = (sin(phase) * 0.62 + noise_state * 0.38) * gain * envelope
	return _wav_from_samples(samples)

func _ambience(duration: float, noise_gain: float, hum_hz: float, hum_gain: float, smoothing: float) -> AudioStreamWAV:
	var count := maxi(1, int(duration * SAMPLE_RATE))
	var samples := PackedFloat32Array()
	samples.resize(count)
	var rng := RandomNumberGenerator.new()
	rng.seed = int(hum_hz * 1709.0)
	var phase := 0.0
	var noise_state := 0.0
	for index in count:
		phase += TAU * hum_hz / float(SAMPLE_RATE)
		noise_state = lerpf(noise_state, rng.randf_range(-1.0, 1.0), 0.025 + smoothing * 0.025)
		var slow_drift := 0.82 + sin(float(index) / float(SAMPLE_RATE) * TAU * 0.17) * 0.18
		samples[index] = noise_state * noise_gain * slow_drift + sin(phase) * hum_gain
	var stream := _wav_from_samples(samples)
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_begin = 0
	stream.loop_end = count
	return stream

func _wav_from_samples(samples: PackedFloat32Array) -> AudioStreamWAV:
	var bytes := PackedByteArray()
	bytes.resize(samples.size() * 2)
	for index in samples.size():
		var value := int(clampf(samples[index], -1.0, 1.0) * 32767.0)
		bytes.encode_s16(index * 2, value)
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = SAMPLE_RATE
	stream.stereo = false
	stream.data = bytes
	return stream

func _native_volume(cue: String) -> float:
	if cue == "transition":
		return -11.0
	if cue in ["fire_master", "summary"]:
		return -7.0
	if cue == "choice" or cue.begins_with("contract_"):
		return -7.0
	if cue == "rain_focus":
		return -14.0
	if cue in ["gauge_start", "paper", "debt"]:
		return -13.0
	return -10.0
