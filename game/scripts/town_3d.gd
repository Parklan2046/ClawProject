class_name WuxiaTown3D
extends SubViewportContainer

var reduce_motion := false
var viewport_3d: SubViewport
var world_root: Node3D
var camera: Camera3D
var moon: MeshInstance3D
var cloud_groups: Array[Node3D] = []
var elapsed := 0.0
var rng := RandomNumberGenerator.new()

var wall_materials: Array[StandardMaterial3D] = []
var wood_material: StandardMaterial3D
var dark_wood_material: StandardMaterial3D
var roof_material: StandardMaterial3D
var roof_edge_material: StandardMaterial3D
var stone_material: StandardMaterial3D
var stone_alt_material: StandardMaterial3D
var window_material: StandardMaterial3D
var lantern_material: StandardMaterial3D
var cloud_material: StandardMaterial3D
var moon_material: StandardMaterial3D
var mountain_material: StandardMaterial3D

func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	stretch = true
	rng.seed = 260725
	_build_materials()
	_build_viewport()
	_build_world()
	set_process(not reduce_motion)

func _build_viewport() -> void:
	viewport_3d = SubViewport.new()
	viewport_3d.name = "TownViewport"
	viewport_3d.own_world_3d = true
	viewport_3d.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	viewport_3d.msaa_3d = Viewport.MSAA_2X
	viewport_3d.scaling_3d_mode = Viewport.SCALING_3D_MODE_BILINEAR
	add_child(viewport_3d)

func _build_world() -> void:
	world_root = Node3D.new()
	world_root.name = "QingshiTown"
	viewport_3d.add_child(world_root)
	_build_environment()
	_build_camera()
	_build_mountains()
	_build_street()
	_build_buildings()
	_build_lanterns()
	_build_moon()
	_build_clouds()

func _build_materials() -> void:
	wall_materials = [
		_material(Color("#514b43"), 0.92),
		_material(Color("#444748"), 0.94),
		_material(Color("#5a5146"), 0.90),
		_material(Color("#3d4548"), 0.95)
	]
	wood_material = _material(Color("#382923"), 0.84)
	dark_wood_material = _material(Color("#171516"), 0.90)
	roof_material = _material(Color("#17212b"), 0.70, 0.16)
	roof_edge_material = _material(Color("#0b1118"), 0.68, 0.20)
	stone_material = _material(Color("#2a3642"), 0.52, 0.18)
	stone_alt_material = _material(Color("#202a34"), 0.62, 0.12)
	mountain_material = _material(Color("#101b24"), 1.0)
	window_material = _emissive_material(Color("#e89242"), 1.15)
	lantern_material = _emissive_material(Color("#ff5d36"), 3.2)
	moon_material = _emissive_material(Color("#cbdce1"), 2.1)

func _build_environment() -> void:
	var world_environment := WorldEnvironment.new()
	var environment := Environment.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("#07101c")
	sky_material.sky_horizon_color = Color("#23384a")
	sky_material.ground_bottom_color = Color("#05080d")
	sky_material.ground_horizon_color = Color("#172735")
	sky_material.sky_curve = 0.18
	sky_material.ground_curve = 0.12
	var sky := Sky.new()
	sky.sky_material = sky_material
	environment.background_mode = Environment.BG_SKY
	environment.sky = sky
	environment.background_energy_multiplier = 0.62
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("#657f9c")
	environment.ambient_light_energy = 0.34
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.fog_enabled = true
	environment.fog_light_color = Color("#1d3243")
	environment.fog_light_energy = 0.58
	environment.fog_density = 0.012
	environment.fog_height = 1.8
	environment.fog_height_density = 0.12
	world_environment.environment = environment
	world_root.add_child(world_environment)

	var moonlight := DirectionalLight3D.new()
	moonlight.name = "Moonlight"
	moonlight.rotation_degrees = Vector3(-52.0, -24.0, 0.0)
	moonlight.light_color = Color("#a9c5e2")
	moonlight.light_energy = 0.82
	moonlight.shadow_enabled = true
	moonlight.directional_shadow_max_distance = 72.0
	world_root.add_child(moonlight)

	var fill := DirectionalLight3D.new()
	fill.name = "WarmFill"
	fill.rotation_degrees = Vector3(-30.0, 156.0, 0.0)
	fill.light_color = Color("#d78c64")
	fill.light_energy = 0.22
	fill.shadow_enabled = false
	world_root.add_child(fill)

func _build_camera() -> void:
	camera = Camera3D.new()
	camera.name = "LoginCamera"
	camera.position = Vector3(0.0, 4.8, 17.5)
	camera.fov = 66.0
	camera.near = 0.15
	camera.far = 180.0
	world_root.add_child(camera)
	camera.look_at(Vector3(0.0, 3.1, -24.0), Vector3.UP)
	camera.current = true

func _build_mountains() -> void:
	var mountain_data := [
		Vector4(-25.0, -73.0, 16.0, 35.0),
		Vector4(-9.0, -82.0, 20.0, 44.0),
		Vector4(13.0, -78.0, 18.0, 39.0),
		Vector4(30.0, -70.0, 14.0, 31.0),
		Vector4(1.0, -98.0, 27.0, 52.0)
	]
	for i in mountain_data.size():
		var data: Vector4 = mountain_data[i]
		var mesh := CylinderMesh.new()
		mesh.top_radius = 0.2
		mesh.bottom_radius = data.z
		mesh.height = data.w
		mesh.radial_segments = 7
		mesh.rings = 1
		var instance := MeshInstance3D.new()
		instance.name = "Mountain%02d" % i
		instance.mesh = mesh
		instance.material_override = mountain_material
		instance.position = Vector3(data.x, data.w * 0.5 - 4.0, data.y)
		instance.rotation_degrees.y = float(i) * 19.0
		world_root.add_child(instance)

func _build_street() -> void:
	_box(world_root, "StreetBase", Vector3(0.0, -0.18, -25.0), Vector3(9.4, 0.35, 86.0), stone_material)
	_box(world_root, "LeftWalk", Vector3(-5.2, 0.02, -25.0), Vector3(1.0, 0.35, 86.0), stone_alt_material)
	_box(world_root, "RightWalk", Vector3(5.2, 0.02, -25.0), Vector3(1.0, 0.35, 86.0), stone_alt_material)

	var stone_mesh := BoxMesh.new()
	stone_mesh.size = Vector3(1.0, 0.08, 1.0)
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.mesh = stone_mesh
	var columns := 7
	var rows := 34
	multimesh.instance_count = columns * rows
	for row in rows:
		for column in columns:
			var index := row * columns + column
			var z := 12.0 - float(row) * 2.15
			var x := (float(column) - 3.0) * 1.28 + (0.42 if row % 2 == 1 else 0.0)
			var scale := Vector3(rng.randf_range(0.96, 1.18), 1.0, rng.randf_range(1.55, 1.92))
			var basis := Basis.IDENTITY.scaled(scale)
			basis = basis.rotated(Vector3.UP, rng.randf_range(-0.035, 0.035))
			multimesh.set_instance_transform(index, Transform3D(basis, Vector3(x, 0.035 + rng.randf_range(-0.012, 0.012), z)))
	var stones := MultiMeshInstance3D.new()
	stones.name = "StreetStones"
	stones.multimesh = multimesh
	stones.material_override = stone_material
	world_root.add_child(stones)

func _build_buildings() -> void:
	for side_value in [-1.0, 1.0]:
		var side: float = side_value
		for row in 10:
			var depth := rng.randf_range(5.8, 7.5)
			var width := rng.randf_range(5.4, 7.0)
			var height := rng.randf_range(3.7, 5.0)
			var x := side * rng.randf_range(7.0, 8.6)
			var z := 9.0 - float(row) * 7.4 + rng.randf_range(-0.65, 0.65)
			var levels := 2 if row % 3 == 1 else 1
			_build_house(side, Vector3(x, 0.0, z), width, depth, height, levels, row)

func _build_house(side: float, origin: Vector3, width: float, depth: float, height: float, levels: int, index: int) -> void:
	var house := Node3D.new()
	house.name = "%sHouse%02d" % ["Left" if side < 0.0 else "Right", index]
	house.position = origin
	world_root.add_child(house)
	var wall_material := wall_materials[index % wall_materials.size()]
	_box(house, "LowerWall", Vector3(0.0, height * 0.5, 0.0), Vector3(width, height, depth), wall_material)
	_add_timber_frame(house, width, depth, height, side)
	_add_roof(house, Vector3(0.0, height + 0.25, 0.0), width, depth)

	if levels == 2:
		var upper_width := width * 0.78
		var upper_depth := depth * 0.78
		var upper_height := height * 0.68
		var upper_y := height + upper_height * 0.5 + 0.35
		_box(house, "UpperWall", Vector3(0.0, upper_y, 0.0), Vector3(upper_width, upper_height, upper_depth), wall_material)
		_add_timber_frame(house, upper_width, upper_depth, upper_y + upper_height * 0.5, side, upper_y - upper_height * 0.5)
		_add_roof(house, Vector3(0.0, upper_y + upper_height * 0.5 + 0.22, 0.0), upper_width, upper_depth)

	_add_facade_details(house, side, width, depth, height)

func _add_timber_frame(parent: Node3D, width: float, depth: float, top_y: float, side: float, base_y: float = 0.0) -> void:
	var inner_x := -side * width * 0.505
	var frame_height := top_y - base_y
	for z_offset in [-depth * 0.34, 0.0, depth * 0.34]:
		_box(parent, "Post", Vector3(inner_x, base_y + frame_height * 0.5, z_offset), Vector3(0.18, frame_height, 0.18), wood_material)
	_box(parent, "TopBeam", Vector3(inner_x, top_y - 0.12, 0.0), Vector3(0.20, 0.24, depth * 0.94), dark_wood_material)
	_box(parent, "MidBeam", Vector3(inner_x, base_y + frame_height * 0.54, 0.0), Vector3(0.20, 0.16, depth * 0.94), wood_material)

func _add_roof(parent: Node3D, position: Vector3, width: float, depth: float) -> void:
	var roof := Node3D.new()
	roof.name = "Roof"
	roof.position = position
	parent.add_child(roof)
	var slope := deg_to_rad(20.0)
	_box(roof, "LeftSlope", Vector3(-width * 0.235, 0.34, 0.0), Vector3(width * 0.59, 0.24, depth * 1.20), roof_material, Vector3(0.0, 0.0, slope))
	_box(roof, "RightSlope", Vector3(width * 0.235, 0.34, 0.0), Vector3(width * 0.59, 0.24, depth * 1.20), roof_material, Vector3(0.0, 0.0, -slope))
	var ridge_mesh := CylinderMesh.new()
	ridge_mesh.top_radius = 0.14
	ridge_mesh.bottom_radius = 0.14
	ridge_mesh.height = depth * 1.25
	ridge_mesh.radial_segments = 8
	var ridge := MeshInstance3D.new()
	ridge.name = "Ridge"
	ridge.mesh = ridge_mesh
	ridge.material_override = roof_edge_material
	ridge.position = Vector3(0.0, 0.76, 0.0)
	ridge.rotation_degrees.x = 90.0
	roof.add_child(ridge)
	for z_end in [-depth * 0.61, depth * 0.61]:
		_box(roof, "Eave", Vector3(0.0, 0.25, z_end), Vector3(width * 1.16, 0.16, 0.16), roof_edge_material)
	for side_value in [-1.0, 1.0]:
		var side: float = side_value
		for strip in 3:
			var x := side * width * (0.13 + float(strip) * 0.17)
			var y := 0.72 - absf(x) * tan(slope)
			var tile_mesh := CylinderMesh.new()
			tile_mesh.top_radius = 0.035
			tile_mesh.bottom_radius = 0.035
			tile_mesh.height = depth * 1.22
			tile_mesh.radial_segments = 6
			var tile_line := MeshInstance3D.new()
			tile_line.name = "TileLine"
			tile_line.mesh = tile_mesh
			tile_line.material_override = roof_edge_material
			tile_line.position = Vector3(x, y, 0.0)
			tile_line.rotation_degrees.x = 90.0
			roof.add_child(tile_line)

func _add_facade_details(parent: Node3D, side: float, width: float, depth: float, height: float) -> void:
	var inner_x := -side * width * 0.515
	_box(parent, "Door", Vector3(inner_x, height * 0.38, 0.0), Vector3(0.14, height * 0.72, depth * 0.24), dark_wood_material)
	for z_offset in [-depth * 0.31, depth * 0.31]:
		_box(parent, "Window", Vector3(inner_x - side * 0.015, height * 0.62, z_offset), Vector3(0.12, height * 0.25, depth * 0.18), window_material)
		for bar in [-0.28, 0.0, 0.28]:
			_box(parent, "WindowBar", Vector3(inner_x - side * 0.03, height * 0.62 + bar * height * 0.22, z_offset), Vector3(0.14, 0.055, depth * 0.19), dark_wood_material)

func _build_lanterns() -> void:
	for row in 12:
		var z := 10.0 - float(row) * 5.7
		for side_value in [-1.0, 1.0]:
			var side: float = side_value
			var post_x := side * 5.45
			var post_mesh := CylinderMesh.new()
			post_mesh.top_radius = 0.055
			post_mesh.bottom_radius = 0.075
			post_mesh.height = 3.4
			post_mesh.radial_segments = 8
			var post := MeshInstance3D.new()
			post.name = "LanternPost"
			post.mesh = post_mesh
			post.material_override = dark_wood_material
			post.position = Vector3(post_x, 1.7, z)
			world_root.add_child(post)
			_box(world_root, "LanternArm", Vector3(post_x - side * 0.34, 3.28, z), Vector3(0.72, 0.08, 0.08), dark_wood_material)
			var lantern_mesh := SphereMesh.new()
			lantern_mesh.radius = 0.24
			lantern_mesh.height = 0.58
			lantern_mesh.radial_segments = 12
			lantern_mesh.rings = 6
			var lantern := MeshInstance3D.new()
			lantern.name = "Lantern"
			lantern.mesh = lantern_mesh
			lantern.material_override = lantern_material
			lantern.position = Vector3(post_x - side * 0.63, 2.98, z)
			world_root.add_child(lantern)
			if row % 3 == 0:
				var light := OmniLight3D.new()
				light.name = "LanternLight"
				light.position = lantern.position
				light.light_color = Color("#ff8a52")
				light.light_energy = 3.4
				light.omni_range = 8.4
				light.shadow_enabled = false
				world_root.add_child(light)

func _build_moon() -> void:
	var mesh := SphereMesh.new()
	mesh.radius = 3.1
	mesh.height = 6.2
	mesh.radial_segments = 24
	mesh.rings = 12
	moon = MeshInstance3D.new()
	moon.name = "Moon"
	moon.mesh = mesh
	moon.material_override = moon_material
	moon.position = Vector3(-13.0, 21.0, -54.0)
	world_root.add_child(moon)

func _build_clouds() -> void:
	var cloud_specs := [
		Vector4(-18.0, 16.5, -34.0, 0.72),
		Vector4(8.0, 19.0, -45.0, 0.46),
		Vector4(-4.0, 13.5, -25.0, 0.92)
	]
	var cloud_shader := Shader.new()
	cloud_shader.code = """
shader_type spatial;
render_mode unshaded, cull_disabled, depth_draw_never;
uniform float opacity = 0.34;
uniform float seed = 0.0;
float hash(vec2 p) {
	return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}
float noise(vec2 p) {
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	return mix(mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x), mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x), f.y);
}
float fbm(vec2 p) {
	float value = 0.0;
	float amplitude = 0.55;
	for (int i = 0; i < 4; i++) {
		value += noise(p) * amplitude;
		p = p * 2.03 + 13.17;
		amplitude *= 0.48;
	}
	return value;
}
void fragment() {
	vec2 p = UV * vec2(4.6, 2.2) + vec2(TIME * 0.018 + seed, seed * 0.37);
	float cloud = smoothstep(0.48, 0.73, fbm(p));
	float edge = smoothstep(0.0, 0.16, UV.y) * smoothstep(0.0, 0.16, 1.0 - UV.y) * smoothstep(0.0, 0.10, UV.x) * smoothstep(0.0, 0.10, 1.0 - UV.x);
	ALBEDO = vec3(0.46, 0.56, 0.66);
	ALPHA = cloud * edge * opacity;
}
"""
	for i in cloud_specs.size():
		var spec: Vector4 = cloud_specs[i]
		var group := Node3D.new()
		group.name = "CloudGroup%02d" % i
		group.position = Vector3(spec.x, spec.y, spec.z)
		group.set_meta("speed", spec.w)
		group.set_meta("start_x", spec.x)
		var cloud_mesh := QuadMesh.new()
		cloud_mesh.size = Vector2(34.0 + float(i) * 7.0, 8.0 + float(i) * 1.5)
		var cloud_instance := MeshInstance3D.new()
		cloud_instance.name = "CloudLayer"
		cloud_instance.mesh = cloud_mesh
		var cloud_shader_material := ShaderMaterial.new()
		cloud_shader_material.shader = cloud_shader
		cloud_shader_material.set_shader_parameter("opacity", 0.30 - float(i) * 0.055)
		cloud_shader_material.set_shader_parameter("seed", float(i) * 7.31)
		cloud_instance.material_override = cloud_shader_material
		group.add_child(cloud_instance)
		world_root.add_child(group)
		cloud_groups.append(group)

func _process(delta: float) -> void:
	elapsed += delta
	for i in cloud_groups.size():
		var group := cloud_groups[i]
		var speed := float(group.get_meta("speed"))
		group.position.x += speed * delta
		if group.position.x > 36.0:
			group.position.x = -36.0
		group.position.y += sin(elapsed * 0.08 + float(i)) * delta * 0.035
	var camera_position := Vector3(
		sin(elapsed * 0.075) * 0.72,
		4.8 + sin(elapsed * 0.052) * 0.16,
		17.5 + cos(elapsed * 0.038) * 0.24
	)
	camera.position = camera_position
	camera.look_at(Vector3(sin(elapsed * 0.045) * 0.42, 3.1, -24.0), Vector3.UP)
	moon.position.x = -13.0 + sin(elapsed * 0.018) * 2.8
	moon.position.y = 21.0 + cos(elapsed * 0.014) * 0.8

func _box(parent: Node, node_name: String, position: Vector3, box_size: Vector3, material: Material, rotation: Vector3 = Vector3.ZERO) -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = box_size
	var instance := MeshInstance3D.new()
	instance.name = node_name
	instance.mesh = mesh
	instance.material_override = material
	instance.position = position
	instance.rotation = rotation
	parent.add_child(instance)
	return instance

func _material(color: Color, roughness: float, metallic: float = 0.0) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	material.metallic = metallic
	return material

func _emissive_material(color: Color, energy: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color.darkened(0.35)
	material.roughness = 0.72
	material.emission_enabled = true
	material.emission = color
	material.emission_energy_multiplier = energy
	return material
