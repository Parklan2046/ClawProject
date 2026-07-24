class_name WuxiaOST
extends AudioStreamPlayer

const MIX_RATE := 22050.0
const BPM := 62.0
const BEAT := 60.0 / BPM
const MELODY := [57, 60, 62, 64, 67, 64, 62, 60, 55, 57, 60, 62, 64, 62, 60, 57]
const BASS := [45, 43, 40, 43]

var generator := AudioStreamGenerator.new()
var playback: AudioStreamGeneratorPlayback
var playhead := 0.0

func _ready() -> void:
	generator.mix_rate = MIX_RATE
	generator.buffer_length = 0.45
	stream = generator
	volume_db = -11.0
	play()
	playback = get_stream_playback() as AudioStreamGeneratorPlayback

func _process(_delta: float) -> void:
	if playback == null:
		return
	var frames := playback.get_frames_available()
	for i in frames:
		var sample := _sample(playhead)
		var pan := sin(playhead * 0.07) * 0.035
		playback.push_frame(Vector2(sample * (1.0 - pan), sample * (1.0 + pan)))
		playhead += 1.0 / MIX_RATE

func _sample(time: float) -> float:
	var beat_index := int(floor(time / BEAT))
	var local := fposmod(time, BEAT)
	var note: int = MELODY[beat_index % MELODY.size()]
	var frequency := 440.0 * pow(2.0, (float(note) - 69.0) / 12.0)
	var attack := minf(local / 0.055, 1.0)
	var release := minf((BEAT - local) / 0.22, 1.0)
	var flute_env := attack * release * (0.72 + sin(local * PI / BEAT) * 0.28)
	var breath := sin(time * 117.31) * sin(time * 73.77) * 0.018
	var flute := (
		sin(TAU * frequency * time)
		+ sin(TAU * frequency * 2.0 * time) * 0.16
		+ breath
	) * flute_env * 0.16
	var pluck_env := attack * exp(-local * 4.1)
	var pluck := (
		sin(TAU * frequency * time)
		+ sin(TAU * frequency * 2.01 * time) * 0.38
		+ sin(TAU * frequency * 3.98 * time) * 0.16
	) * pluck_env * 0.16
	var bass_index := int(floor(float(beat_index) / 4.0)) % BASS.size()
	var bass_frequency := 440.0 * pow(2.0, (float(BASS[bass_index]) - 69.0) / 12.0)
	var bass_phase := fposmod(time, BEAT * 4.0)
	var bass_env := minf(bass_phase / 0.6, 1.0) * minf((BEAT * 4.0 - bass_phase) / 1.2, 1.0)
	var drone := (sin(TAU * bass_frequency * time) + sin(TAU * bass_frequency * 0.5 * time) * 0.38) * bass_env * 0.075
	var bell_phase := fposmod(time, BEAT * 8.0)
	var bell := 0.0
	if bell_phase < 2.4:
		var bell_frequency := frequency * 2.0
		bell = (
			sin(TAU * bell_frequency * time)
			+ sin(TAU * bell_frequency * 2.71 * time) * 0.32
		) * exp(-bell_phase * 2.5) * 0.08
	var fade_in := minf(time / 3.5, 1.0)
	return clampf((flute + pluck + drone + bell) * fade_in, -0.72, 0.72)
