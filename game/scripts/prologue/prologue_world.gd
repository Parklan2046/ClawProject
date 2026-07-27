extends Node3D

var camera: Camera3D
var key_light: DirectionalLight3D
var warm_lights: Array[OmniLight3D] = []
var focus_points: Dictionary = {}
var camera_home := Vector3(0, 4.3, 9.2)
var camera_target := Vector3(0, 2.0, 0)
var time := 0.0
var threshold_door_root: Node3D
var threshold_door_pivot: Node3D
var threshold_door_light: OmniLight3D

func _ready() -> void:
	set_process(true)

func build_threshold_intro() -> void:
	_clear_world()
	_setup_world(Color("#050a10"), Color("#22384a"), 0.42)
	camera.fov = 43.0
	camera_home = Vector3(0.0, 2.72, 9.8)
	camera_target = Vector3(0.0, 2.48, 0.15)
	_place_camera(camera_home, camera_target)
	var threshold_mobile := get_viewport().get_visible_rect().size.x < 760.0
	var backdrop_path := "res://assets/bg/prologue-hk-door-2026-mobile-v1.png" if threshold_mobile else "res://assets/bg/prologue-hk-door-2026-v1.png"
	_add_background(backdrop_path)
	key_light.light_color = Color("#7697ad")
	key_light.light_energy = 0.92

	threshold_door_root = Node3D.new()
	threshold_door_root.name = "ThresholdDoorAssembly"
	threshold_door_root.scale = Vector3(0.70, 1.0, 0.70) if threshold_mobile else Vector3.ONE
	add_child(threshold_door_root)

	var frame_color := Color("#171c21")
	var frame_edge := Color("#30383e")
	_box_child(threshold_door_root, "DoorFrameLeft", Vector3(0.30, 5.35, 0.42), Vector3(-1.92, 2.58, 0.34), frame_color, 0.76, 0.34)
	_box_child(threshold_door_root, "DoorFrameRight", Vector3(0.30, 5.35, 0.42), Vector3(1.92, 2.58, 0.34), frame_color, 0.76, 0.34)
	_box_child(threshold_door_root, "DoorFrameTop", Vector3(4.14, 0.34, 0.44), Vector3(0.0, 5.10, 0.34), frame_edge, 0.72, 0.32)
	_box_child(threshold_door_root, "DoorThreshold", Vector3(3.86, 0.14, 0.62), Vector3(0.0, -0.02, 0.48), Color("#343a3c"), 0.72, 0.28)

	threshold_door_pivot = Node3D.new()
	threshold_door_pivot.name = "ThresholdDoorHinge"
	threshold_door_pivot.position = Vector3(-1.76, 2.54, 0.48)
	threshold_door_root.add_child(threshold_door_pivot)

	var door_color := Color("#2a343c")
	_box_child(threshold_door_pivot, "DoorLeaf", Vector3(3.52, 4.94, 0.20), Vector3(1.76, 0.0, 0.0), door_color, 0.82, 0.32)
	_box_child(threshold_door_pivot, "DoorInset", Vector3(3.12, 4.48, 0.05), Vector3(1.76, 0.0, 0.13), Color("#202a31"), 0.66, 0.38)
	_box_child(threshold_door_pivot, "DoorKickPlate", Vector3(3.10, 0.72, 0.05), Vector3(1.76, -1.78, 0.17), Color("#4a5358"), 0.90, 0.24)

	var glass := _box_child(
		threshold_door_pivot,
		"DoorWiredGlass",
		Vector3(1.42, 1.22, 0.06),
		Vector3(1.76, 0.92, 0.18),
		Color(0.08, 0.15, 0.19, 0.92),
		0.25,
		0.18,
		Color(0.08, 0.20, 0.25, 0.35)
	)
	glass.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for index in 5:
		_box_child(
			threshold_door_pivot,
			"GlassWireV%d" % index,
			Vector3(0.018, 1.14, 0.015),
			Vector3(1.28 + index * 0.24, 0.92, 0.225),
			Color(0.55, 0.62, 0.64, 0.44),
			0.82,
			0.24
		)
	for index in 4:
		_box_child(
			threshold_door_pivot,
			"GlassWireH%d" % index,
			Vector3(1.34, 0.018, 0.015),
			Vector3(1.76, 0.56 + index * 0.24, 0.225),
			Color(0.55, 0.62, 0.64, 0.44),
			0.82,
			0.24
		)

	_box_child(threshold_door_pivot, "DoorHandleBack", Vector3(0.18, 0.72, 0.11), Vector3(2.88, -0.18, 0.24), Color("#11161a"), 0.80, 0.26)
	_box_child(threshold_door_pivot, "DoorHandle", Vector3(0.15, 0.58, 0.15), Vector3(2.88, -0.18, 0.36), Color("#a2a09a"), 0.94, 0.18)
	_box_child(threshold_door_pivot, "DeliverySticker", Vector3(0.58, 0.72, 0.025), Vector3(0.72, -0.62, 0.235), Color("#78322f"), 0.04, 0.66)
	_box_child(threshold_door_pivot, "DeliveryStickerLine", Vector3(0.34, 0.035, 0.014), Vector3(0.72, -0.52, 0.255), Color("#d2b995"), 0.0, 0.72)
	for index in 5:
		_box_child(
			threshold_door_pivot,
			"DoorVent%d" % index,
			Vector3(1.06, 0.045, 0.025),
			Vector3(1.76, -1.05 + index * 0.13, 0.235),
			Color("#586067"),
			0.74,
			0.28
		)

	_box_child(threshold_door_root, "DoorLightSeamRight", Vector3(0.055, 4.76, 0.07), Vector3(1.79, 2.54, 0.39), Color("#f1c47e"), 0.0, 0.18, Color("#f1b75f"))
	_box_child(threshold_door_root, "DoorLightSeamBottom", Vector3(3.48, 0.055, 0.07), Vector3(0.0, 0.08, 0.39), Color("#eebc72"), 0.0, 0.18, Color("#e8a94d"))
	_add_omni(Vector3(-1.25, 3.35, 4.55), Color("#6f94ad"), 2.35, 8.0)
	threshold_door_light = _add_omni(Vector3(0.0, 2.5, -0.25), Color("#f3bd75"), 1.15, 5.2)
	_box_child(threshold_door_root, "WetEntryMat", Vector3(3.58, 0.035, 1.38), Vector3(0.0, 0.04, 1.08), Color(0.04, 0.055, 0.06, 0.74), 0.12, 0.24)

func open_threshold_door(reduce_motion: bool) -> void:
	if threshold_door_pivot == null or not is_instance_valid(threshold_door_pivot):
		return
	if reduce_motion:
		threshold_door_pivot.rotation_degrees.y = 82.0
		camera.position = Vector3(0.0, 2.72, 7.25)
		if threshold_door_light != null:
			threshold_door_light.light_energy = 3.4
		return
	var tween := create_tween().set_parallel(true)
	tween.set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_IN_OUT)
	tween.tween_property(threshold_door_pivot, "rotation_degrees:y", 82.0, 1.35)
	tween.tween_property(camera, "position", Vector3(0.0, 2.72, 7.25), 1.55)
	if threshold_door_light != null:
		tween.tween_property(threshold_door_light, "light_energy", 3.4, 0.72)
	await tween.finished

func build_modern_restaurant() -> void:
	_clear_world()
	_setup_world(Color("#071019"), Color("#263b4d"), 0.54)
	camera_home = Vector3(0.2, 4.15, 9.8)
	camera_target = Vector3(0, 1.45, 0.65)
	_place_camera(camera_home, camera_target)
	_add_background("res://assets/bg/prologue-office-v1.png")

	var desk_wood := Color("#2a2522")
	var desk_edge := Color("#17191d")
	_box("DeskTop", Vector3(5.2, 0.16, 1.95), Vector3(-0.55, 1.05, 1.38), desk_wood, 0.05, 0.38)
	_box("DeskFront", Vector3(5.0, 0.66, 0.12), Vector3(-0.55, 0.70, 2.28), Color("#24211f"), 0.06, 0.52)
	for x in [-2.75, 1.65]:
		_box("DeskLeg", Vector3(0.18, 1.02, 0.18), Vector3(x, 0.52, 0.70), desk_edge, 0.16, 0.34)
		_box("DeskLeg", Vector3(0.18, 1.02, 0.18), Vector3(x, 0.52, 2.02), desk_edge, 0.16, 0.34)

	_box("LaptopBase", Vector3(1.72, 0.075, 1.02), Vector3(-0.70, 1.18, 1.18), Color("#1c222a"), 0.66, 0.24)
	var screen := _box("LaptopScreen", Vector3(1.70, 1.02, 0.07), Vector3(-0.70, 1.76, 0.70), Color("#10252b"), 0.24, 0.22, Color("#153b43"))
	screen.rotation_degrees.x = -8.0
	for index in 4:
		var screen_line := _box(
			"ScreenLine%d" % index,
			Vector3(1.18 - index * 0.12, 0.055, 0.012),
			Vector3(-0.70, 1.98 - index * 0.16, 0.742),
			Color("#7cb0b4") if index < 2 else Color("#b6534a"),
			0.0,
			0.30,
			Color("#285b61") if index < 2 else Color("#702b2a")
		)
		screen_line.rotation_degrees.x = -8.0
	for row in 3:
		for column in 7:
			_box(
				"Key_%d_%d" % [row, column],
				Vector3(0.12, 0.018, 0.10),
				Vector3(-1.05 + column * 0.15, 1.229, 1.15 + row * 0.13),
				Color("#303741"),
				0.24,
				0.38
			)

	var phone := _box("Phone", Vector3(0.46, 0.045, 0.82), Vector3(0.70, 1.17, 1.35), Color("#171b21"), 0.55, 0.22)
	phone.rotation_degrees.y = -11.0
	var phone_screen := _box("PhoneScreen", Vector3(0.39, 0.014, 0.67), Vector3(0.70, 1.202, 1.35), Color("#611d20"), 0.08, 0.18, Color("#bb3936"))
	phone_screen.rotation_degrees.y = -11.0
	for index in 3:
		_box("PhoneNotice%d" % index, Vector3(0.22 - index * 0.035, 0.010, 0.025), Vector3(0.70, 1.216, 1.20 + index * 0.13), Color("#f3c1ad"), 0.0, 0.3, Color("#c86b5f"))

	for index in 9:
		var paper := _box(
			"Receipt%d" % index,
			Vector3(0.42, 0.018, 0.68),
			Vector3(-2.70 + index * 0.31, 1.16 + index * 0.004, 1.34 + sin(index * 1.3) * 0.25),
			Color("#c9c4b8")
		)
		paper.rotation_degrees.y = -22.0 + index * 6.0
		for line_index in 3:
			_box(
				"ReceiptLine_%d_%d" % [index, line_index],
				Vector3(0.22, 0.008, 0.018),
				Vector3(paper.position.x, paper.position.y + 0.018, paper.position.z - 0.17 + line_index * 0.15),
				Color("#666a6b")
			).rotation_degrees.y = paper.rotation_degrees.y

	_cylinder("CoffeeCup", 0.23, 0.42, Vector3(1.45, 1.31, 1.02), Color("#35383b"), 0.16, 0.34)
	_cylinder("ColdCoffee", 0.19, 0.015, Vector3(1.45, 1.53, 1.02), Color("#1d110c"), 0.0, 0.18)

	_add_omni(Vector3(-0.8, 3.5, 1.2), Color("#db9c61"), 3.6, 7.0)
	_add_omni(Vector3(-3.8, 2.4, -0.5), Color("#5d97ba"), 2.3, 8.0)
	focus_points = {
		"phone": Vector3(0.70, 1.20, 1.35),
		"receipts": Vector3(-2.0, 1.18, 1.35),
		"window": Vector3(-3.3, 2.8, -1.8)
	}

func build_song_home() -> void:
	_clear_world()
	_setup_world(Color("#111116"), Color("#554334"), 0.72)
	# Match the painting's low, almost level one-point perspective. The previous
	# camera looked down from above, so every foreground prop appeared pasted on.
	camera.fov = 44.0
	camera_home = Vector3(0.0, 2.38, 10.85)
	camera_target = Vector3(0.0, 1.95, 0.10)
	_place_camera(camera_home, camera_target)
	_add_background("res://assets/bg/prologue-song-home-v1.png")
	key_light.light_color = Color("#c6a17d")
	key_light.light_energy = 0.72

	var wood := Color("#4b3323")
	var dark_wood := Color("#271a13")

	_box("TableShadow", Vector3(3.55, 0.025, 1.42), Vector3(0.25, 0.035, 0.82), Color(0.02, 0.015, 0.012, 0.34))
	_box("Table", Vector3(3.25, 0.16, 1.25), Vector3(0.25, 0.70, 0.80), Color("#34231a"), 0.0, 0.66)
	_box("TableEdge", Vector3(3.10, 0.14, 0.10), Vector3(0.25, 0.59, 1.37), dark_wood, 0.0, 0.62)
	for x in [-1.05, 1.55]:
		for z in [0.35, 1.25]:
			_box("TableLeg", Vector3(0.15, 0.64, 0.15), Vector3(x, 0.32, z), dark_wood)

	_cylinder("StoveShadow", 1.00, 0.025, Vector3(-2.72, 0.04, 1.02), Color(0.02, 0.015, 0.012, 0.34))
	_box("StoveBase", Vector3(1.75, 0.90, 1.28), Vector3(-2.72, 0.45, 1.02), Color("#2b2926"), 0.0, 0.98)
	for row in 3:
		for column in 3:
			_box(
				"StoveBrick_%d_%d" % [row, column],
				Vector3(0.50, 0.20, 0.055),
				Vector3(-3.22 + column * 0.50 + (0.12 if row % 2 else 0.0), 0.20 + row * 0.23, 1.69),
				Color("#51473d") if (row + column) % 2 == 0 else Color("#403b36"),
				0.0,
				0.94
			)
	_box("FireMouth", Vector3(0.58, 0.35, 0.08), Vector3(-2.72, 0.38, 1.70), Color("#171311"), 0.0, 1.0)
	for index in 3:
		var log := _cylinder("FireLog%d" % index, 0.060, 0.46, Vector3(-2.88 + index * 0.16, 0.33, 1.63), Color("#3a2117"), 0.0, 0.95)
		log.rotation_degrees.z = 90.0
	for index in 3:
		var flame := _cylinder(
			"Flame%d" % index,
			0.075 - index * 0.010,
			0.25 + index * 0.06,
			Vector3(-2.88 + index * 0.16, 0.58 + index * 0.04, 1.61),
			Color(0.93, 0.27 + index * 0.08, 0.08, 0.76),
			0.0,
			0.24,
			Color("#f47b35")
		)
		flame.rotation_degrees.z = -8.0 + index * 8.0
	_cylinder("StoveRing", 0.50, 0.14, Vector3(-2.72, 0.98, 1.02), Color("#292826"), 0.06, 0.78)
	_add_omni(Vector3(-2.72, 1.20, 1.23), Color("#ff823e"), 2.2, 3.4)

	_cylinder("SteamerBottom", 0.58, 0.28, Vector3(-0.62, 0.91, 0.70), Color("#755033"), 0.0, 0.72)
	_cylinder("SteamerRim", 0.60, 0.055, Vector3(-0.62, 1.07, 0.70), Color("#9a6a42"), 0.0, 0.64)
	var steamer_top := _cylinder("SteamerTop", 0.58, 0.24, Vector3(-0.62, 1.22, 0.70), Color("#66452e"), 0.0, 0.74)
	steamer_top.rotation_degrees.z = 4.0
	for index in 9:
		var slat := _box("SteamerSlat%d" % index, Vector3(0.035, 0.26, 0.92), Vector3(-0.98 + index * 0.09, 1.22, 0.70), Color("#7d5638"))
		slat.rotation_degrees.z = 90.0
	_box("SteamerBrokenSlat", Vector3(0.04, 0.035, 0.48), Vector3(-1.05, 1.38, 0.89), Color("#6f462a")).rotation_degrees.y = 22.0

	_sphere("CoinPouch", 0.18, Vector3(1.16, 0.89, 0.63), Color("#44231f"), 0.0, 0.82)
	_box("PouchTie", Vector3(0.09, 0.13, 0.09), Vector3(1.16, 1.05, 0.63), Color("#2e1916"))
	var debt := _box("DebtPaper", Vector3(0.60, 0.020, 0.78), Vector3(0.28, 0.79, 0.85), Color("#cdbf9d"))
	debt.rotation_degrees.y = -8.0
	_label_3d("欠", Vector3(0.28, 0.84, 0.80), 24, Color("#8f2925"))
	for index in 4:
		_box("DebtLine%d" % index, Vector3(0.30 - index * 0.025, 0.008, 0.018), Vector3(0.28, 0.832, 0.68 + index * 0.10), Color("#755c4b")).rotation_degrees.y = debt.rotation_degrees.y

	_cylinder("SackShadow", 0.56, 0.025, Vector3(2.45, 0.035, 0.95), Color(0.02, 0.015, 0.012, 0.30))
	_sphere("FlourSack", 0.48, Vector3(2.45, 0.47, 0.95), Color("#625b50"), 0.0, 0.98)
	_box("SackTie", Vector3(0.18, 0.13, 0.18), Vector3(2.45, 0.94, 0.95), Color("#51412f"))
	focus_points = {
		"coins": Vector3(1.16, 0.92, 0.63),
		"steamer": Vector3(-0.62, 1.16, 0.70),
		"debt": Vector3(0.28, 0.82, 0.85),
		"stove": Vector3(-2.72, 0.82, 1.02)
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
	threshold_door_root = null
	threshold_door_pivot = null
	threshold_door_light = null

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

func _add_background(texture_path: String) -> void:
	var texture: Texture2D = load(texture_path)
	var mesh := QuadMesh.new()
	var height := 10.8
	var aspect := float(texture.get_width()) / float(maxi(1, texture.get_height()))
	mesh.size = Vector2(height * aspect, height)
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.albedo_texture = texture
	material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.render_priority = -100
	mesh.material = material
	var instance := MeshInstance3D.new()
	instance.name = "CinematicBackground"
	instance.mesh = mesh
	instance.position = Vector3(0, 0, -12)
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	camera.add_child(instance)

func _box(node_name: String, size_value: Vector3, position_value: Vector3, color: Color, metallic := 0.0, roughness := 0.82, emission := Color.TRANSPARENT) -> MeshInstance3D:
	return _box_child(self, node_name, size_value, position_value, color, metallic, roughness, emission)

func _box_child(parent: Node, node_name: String, size_value: Vector3, position_value: Vector3, color: Color, metallic := 0.0, roughness := 0.82, emission := Color.TRANSPARENT) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size_value
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.position = position_value
	instance.material_override = _material(color, metallic, roughness, emission)
	parent.add_child(instance)
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
