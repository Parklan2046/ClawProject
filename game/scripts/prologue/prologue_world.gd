extends Node3D

var camera: Camera3D
var key_light: DirectionalLight3D
var warm_lights: Array[OmniLight3D] = []
var focus_points: Dictionary = {}
var camera_home := Vector3(0, 4.3, 9.2)
var camera_target := Vector3(0, 2.0, 0)
var time := 0.0

func _ready() -> void:
	set_process(true)

func build_modern_restaurant() -> void:
	_clear_world()
	_setup_world(Color("#09121d"), Color("#253d54"), 0.62)
	camera_home = Vector3(0.4, 4.5, 9.6)
	camera_target = Vector3(0, 1.7, -0.4)
	_place_camera(camera_home, camera_target)

	_box("Floor", Vector3(12, 0.18, 8), Vector3(0, -0.1, 0), Color("#1b2027"), 0.12, 0.82)
	_box("BackWall", Vector3(12, 5.8, 0.18), Vector3(0, 2.8, -3.7), Color("#171c22"), 0.0, 0.94)
	_box("LeftWall", Vector3(0.18, 5.8, 8), Vector3(-5.9, 2.8, 0), Color("#11161c"), 0.0, 0.95)
	_box("Counter", Vector3(6.4, 1.05, 1.1), Vector3(1.6, 0.55, -1.75), Color("#302820"), 0.0, 0.58)
	_box("CounterTop", Vector3(6.7, 0.10, 1.3), Vector3(1.6, 1.11, -1.75), Color("#5f554a"), 0.12, 0.38)
	_box("Desk", Vector3(3.9, 0.15, 1.9), Vector3(-1.45, 1.12, 1.25), Color("#3a3027"), 0.0, 0.48)
	for x in [-2.85, -0.05]:
		_box("DeskLeg", Vector3(0.16, 1.1, 0.16), Vector3(x, 0.55, 0.62), Color("#241d19"))
		_box("DeskLeg", Vector3(0.16, 1.1, 0.16), Vector3(x, 0.55, 1.88), Color("#241d19"))
	_box("Laptop", Vector3(1.45, 0.07, 0.88), Vector3(-1.45, 1.25, 1.15), Color("#252b33"), 0.55, 0.28)
	var screen := _box("LaptopScreen", Vector3(1.42, 0.88, 0.07), Vector3(-1.45, 1.75, 0.72), Color("#193f48"), 0.05, 0.30, Color("#2e98a8"))
	screen.rotation_degrees.x = -8.0
	_box("Phone", Vector3(0.42, 0.035, 0.76), Vector3(0.15, 1.24, 1.4), Color("#20242b"), 0.42, 0.25, Color("#a72f28"))
	for index in 7:
		var paper := _box("Receipt%d" % index, Vector3(0.34, 0.018, 0.62), Vector3(-3.2 + index * 0.43, 1.23, 1.18 + sin(index) * 0.22), Color("#d7d1c3"))
		paper.rotation_degrees.y = -18.0 + index * 7.0
	for x in [-3.9, -1.35, 1.2, 3.75]:
		_box("WindowFrame", Vector3(0.09, 3.1, 0.12), Vector3(x, 3.25, -3.56), Color("#11151a"))
	for x in [-2.65, -0.1, 2.45]:
		_box("RainWindow", Vector3(2.38, 3.0, 0.05), Vector3(x, 3.25, -3.54), Color(0.10, 0.22, 0.33, 0.58), 0.15, 0.18, Color("#173b59"))
	for index in 10:
		var streak := _box("Rain%d" % index, Vector3(0.018, 0.48 + fmod(index, 3) * 0.18, 0.025), Vector3(-4.7 + index * 0.95, 2.1 + fmod(index * 0.61, 2.2), -3.48), Color("#8bb5c8"), 0.0, 0.2, Color("#507e98"))
		streak.rotation_degrees.z = -9.0
	_label_3d("LAST ORDER", Vector3(2.0, 3.82, -3.42), 58, Color("#d95d43"))
	_label_3d("03:17", Vector3(-4.2, 4.75, -3.40), 36, Color("#87b4c8"))
	_add_omni(Vector3(-1.5, 3.6, 1.2), Color("#df9f66"), 4.2, 7.0)
	_add_omni(Vector3(2.3, 2.8, -2.1), Color("#6aa7c2"), 3.0, 8.0)
	focus_points = {
		"phone": Vector3(0.15, 1.25, 1.4),
		"receipts": Vector3(-2.0, 1.25, 1.2),
		"window": Vector3(1.6, 3.2, -3.2)
	}

func build_song_home() -> void:
	_clear_world()
	_setup_world(Color("#111116"), Color("#514337"), 0.82)
	camera_home = Vector3(0, 4.05, 9.15)
	camera_target = Vector3(0, 1.75, -0.45)
	_place_camera(camera_home, camera_target)

	var wood := Color("#4b3323")
	var dark_wood := Color("#271a13")
	var plaster := Color("#8e806c")
	var stone := Color("#4a4742")
	_box("Floor", Vector3(11.8, 0.16, 7.8), Vector3(0, -0.08, 0), Color("#382a20"), 0.0, 0.78)
	for index in 13:
		_box("FloorBoard%d" % index, Vector3(0.82, 0.035, 7.5), Vector3(-5.0 + index * 0.84, 0.02, 0), Color("#4a3426") if index % 2 == 0 else Color("#412d22"), 0.0, 0.72)
	_box("BackWall", Vector3(11.8, 5.6, 0.20), Vector3(0, 2.7, -3.65), plaster, 0.0, 0.98)
	_box("LeftWall", Vector3(0.20, 5.6, 7.8), Vector3(-5.8, 2.7, 0), Color("#736653"), 0.0, 0.98)
	for x in [-5.2, -2.6, 0.0, 2.6, 5.2]:
		_box("Beam", Vector3(0.24, 5.6, 0.26), Vector3(x, 2.7, -3.46), dark_wood)
	_box("CeilingBeam", Vector3(11.5, 0.28, 0.34), Vector3(0, 5.2, -3.4), dark_wood)
	_box("Door", Vector3(2.0, 4.0, 0.14), Vector3(3.7, 2.0, -3.48), Color("#37231a"), 0.0, 0.64)
	for y in [0.9, 1.65, 2.4, 3.15]:
		_box("DoorBrace", Vector3(1.7, 0.08, 0.10), Vector3(3.7, y, -3.36), wood)
	for x in [3.12, 3.7, 4.28]:
		_box("DoorBrace", Vector3(0.08, 3.5, 0.10), Vector3(x, 2.0, -3.36), wood)
	_box("Table", Vector3(3.3, 0.20, 1.45), Vector3(0.55, 1.05, 0.42), wood, 0.0, 0.54)
	for x in [-0.75, 1.85]:
		for z in [-0.02, 0.86]:
			_box("TableLeg", Vector3(0.17, 1.0, 0.17), Vector3(x, 0.52, z), dark_wood)
	_box("Shelf", Vector3(3.6, 0.18, 0.65), Vector3(-2.9, 2.85, -3.1), wood)
	_box("Shelf", Vector3(3.6, 0.18, 0.65), Vector3(-2.9, 1.75, -3.1), wood)
	for x in [-4.4, -1.4]:
		_box("ShelfPost", Vector3(0.16, 2.6, 0.16), Vector3(x, 2.15, -3.02), dark_wood)
	for index in 5:
		_cylinder("Jar%d" % index, 0.28 + index % 2 * 0.05, 0.56, Vector3(-4.05 + index * 0.67, 2.18, -2.94), Color("#6e5841"))
	_box("StoveBase", Vector3(2.15, 1.28, 1.5), Vector3(-3.62, 0.64, 1.65), stone, 0.0, 0.90)
	_cylinder("StoveRing", 0.64, 0.20, Vector3(-3.62, 1.36, 1.65), Color("#2f2c29"), 0.08, 0.68)
	_cylinder("StoveFire", 0.36, 0.08, Vector3(-3.62, 1.48, 1.65), Color("#c45a2f"), 0.0, 0.35, Color("#e97636"))
	_add_omni(Vector3(-3.62, 1.92, 1.65), Color("#ff8b43"), 5.0, 4.6)
	_cylinder("SteamerBottom", 0.73, 0.32, Vector3(-1.6, 1.34, 0.42), Color("#8a613b"), 0.0, 0.66)
	var steamer_top := _cylinder("SteamerTop", 0.73, 0.30, Vector3(-1.6, 1.67, 0.42), Color("#9c7045"), 0.0, 0.62)
	steamer_top.rotation_degrees.z = 4.0
	for index in 7:
		var slat := _box("SteamerSlat%d" % index, Vector3(0.04, 0.34, 1.18), Vector3(-1.98 + index * 0.13, 1.68, 0.42), Color("#bf9161"))
		slat.rotation_degrees.z = 90.0
	_sphere("CoinPouch", 0.24, Vector3(1.50, 1.37, 0.15), Color("#4c2823"), 0.0, 0.78)
	var debt := _box("DebtPaper", Vector3(0.68, 0.025, 0.92), Vector3(0.55, 1.19, 0.38), Color("#d8c9a5"))
	debt.rotation_degrees.y = -8.0
	_label_3d("欠", Vector3(0.55, 1.23, 0.34), 30, Color("#8f2925"))
	_sphere("FlourSack", 0.64, Vector3(3.0, 0.70, 1.65), Color("#a79a80"), 0.0, 0.96)
	_box("SackTie", Vector3(0.24, 0.16, 0.24), Vector3(3.0, 1.34, 1.65), Color("#6c543c"))
	_cylinder("Lantern", 0.34, 0.78, Vector3(2.45, 3.62, -2.55), Color("#a82f28"), 0.0, 0.42, Color("#c74731"))
	_box("LanternTop", Vector3(0.70, 0.10, 0.70), Vector3(2.45, 4.04, -2.55), dark_wood)
	_add_omni(Vector3(2.45, 3.45, -2.30), Color("#ff9a55"), 4.0, 5.8)
	for index in 5:
		var steam := _cylinder("Steam%d" % index, 0.035 + index * 0.008, 0.7 + index * 0.15, Vector3(-1.85 + index * 0.13, 2.05 + index * 0.22, 0.44), Color(0.75, 0.78, 0.76, 0.18), 0.0, 1.0)
		steam.rotation_degrees.z = -12.0 + index * 6.0
	focus_points = {
		"coins": Vector3(1.50, 1.35, 0.15),
		"steamer": Vector3(-1.60, 1.55, 0.42),
		"debt": Vector3(0.55, 1.22, 0.38),
		"stove": Vector3(-3.62, 1.34, 1.65)
	}

func focus(id: String) -> void:
	if not focus_points.has(id):
		return
	var point: Vector3 = focus_points[id]
	var direction := (camera_home - point).normalized()
	var target_position := point + direction * 4.4 + Vector3(0, 1.1, 0)
	var tween := create_tween().set_parallel(true)
	tween.set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	tween.tween_property(camera, "position", target_position, 0.65)
	tween.tween_method(func(weight: float) -> void: camera.look_at(lerp(camera_target, point, weight)), 0.0, 1.0, 0.65)

func reset_camera() -> void:
	var start_target := camera_target
	var tween := create_tween().set_parallel(true)
	tween.set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
	tween.tween_property(camera, "position", camera_home, 0.65)
	tween.tween_method(func(weight: float) -> void: camera.look_at(lerp(start_target, camera_target, weight)), 0.0, 1.0, 0.65)

func _process(delta: float) -> void:
	time += delta
	for index in warm_lights.size():
		var light := warm_lights[index]
		if is_instance_valid(light):
			light.light_energy = light.get_meta("base_energy", 3.0) * (0.93 + sin(time * (3.1 + index * 0.37)) * 0.07)

func _clear_world() -> void:
	for child in get_children():
		child.queue_free()
	warm_lights.clear()
	focus_points.clear()

func _setup_world(background: Color, ambient: Color, ambient_energy: float) -> void:
	var world_environment := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = background
	environment.background_energy_multiplier = 0.72
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = ambient
	environment.ambient_light_energy = ambient_energy
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world_environment.environment = environment
	add_child(world_environment)

	camera = Camera3D.new()
	camera.fov = 48.0
	camera.current = true
	add_child(camera)

	key_light = DirectionalLight3D.new()
	key_light.rotation_degrees = Vector3(-48, -28, 0)
	key_light.light_color = Color("#a9c7df")
	key_light.light_energy = 1.05
	key_light.shadow_enabled = true
	add_child(key_light)

func _place_camera(position_value: Vector3, target: Vector3) -> void:
	camera.position = position_value
	camera.look_at(target)

func _box(node_name: String, size_value: Vector3, position_value: Vector3, color: Color, metallic := 0.0, roughness := 0.82, emission := Color.TRANSPARENT) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size_value
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.position = position_value
	instance.material_override = _material(color, metallic, roughness, emission)
	add_child(instance)
	return instance

func _cylinder(node_name: String, radius: float, height: float, position_value: Vector3, color: Color, metallic := 0.0, roughness := 0.82, emission := Color.TRANSPARENT) -> MeshInstance3D:
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = height
	mesh.radial_segments = 24
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.position = position_value
	instance.material_override = _material(color, metallic, roughness, emission)
	add_child(instance)
	return instance

func _sphere(node_name: String, radius: float, position_value: Vector3, color: Color, metallic := 0.0, roughness := 0.82) -> MeshInstance3D:
	var mesh := SphereMesh.new()
	mesh.radius = radius
	mesh.height = radius * 1.6
	mesh.radial_segments = 24
	mesh.rings = 12
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.position = position_value
	instance.material_override = _material(color, metallic, roughness)
	add_child(instance)
	return instance

func _material(color: Color, metallic := 0.0, roughness := 0.82, emission := Color.TRANSPARENT) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.metallic = metallic
	material.roughness = roughness
	if color.a < 0.99:
		material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	if emission.a > 0.0:
		material.emission_enabled = true
		material.emission = emission
		material.emission_energy_multiplier = 1.8
	return material

func _add_omni(position_value: Vector3, color: Color, energy: float, range_value: float) -> OmniLight3D:
	var light := OmniLight3D.new()
	light.position = position_value
	light.light_color = color
	light.light_energy = energy
	light.omni_range = range_value
	light.shadow_enabled = false
	light.set_meta("base_energy", energy)
	add_child(light)
	warm_lights.append(light)
	return light

func _label_3d(text_value: String, position_value: Vector3, size_value: int, color: Color) -> Label3D:
	var label := Label3D.new()
	label.text = text_value
	label.position = position_value
	label.font = load("res://assets/fonts/NotoSansTC-Variable.ttf")
	label.font_size = size_value
	label.modulate = color
	label.outline_size = 6
	label.outline_modulate = Color(0, 0, 0, 0.7)
	add_child(label)
	return label
