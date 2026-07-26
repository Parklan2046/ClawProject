class_name WuxiaTown3D
extends SubViewportContainer

var reduce_motion := false
var viewport_3d: SubViewport
var world_root: Node3D
var camera: Camera3D
var cloud_groups: Array[Node3D] = []
var banner_nodes: Array[Node3D] = []
var fire_nodes: Array[MeshInstance3D] = []
var elapsed := 0.0
var rng := RandomNumberGenerator.new()

var wall_materials: Array[Material] = []
var wood_material: Material
var dark_wood_material: Material
var roof_material: Material
var roof_edge_material: Material
var stone_material: Material
var stone_alt_material: Material
var window_material: Material
var lantern_material: Material
var banner_material: Material
var brass_material: Material
var earth_material: Material
var earth_alt_material: Material

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
	viewport_3d.transparent_bg = true
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
	_build_street()
	_build_buildings()
	_build_lanterns()
	_build_fire_braziers()
	_build_clouds()

func _build_materials() -> void:
	wall_materials = [
		_surface_material(Color("#493b32"), "plaster", 0.94),
		_surface_material(Color("#4c5556"), "plaster", 0.96),
		_surface_material(Color("#796652"), "plaster", 0.92),
		_surface_material(Color("#414d50"), "plaster", 0.97)
	]
	wood_material = _surface_material(Color("#3b241c"), "wood", 0.84)
	dark_wood_material = _material(Color("#171516"), 0.90)
	roof_material = _surface_material(Color("#1a2b39"), "tiles", 0.66, 0.18)
	roof_edge_material = _material(Color("#0a1219"), 0.62, 0.24)
	stone_material = _surface_material(Color("#354554"), "stone", 0.48, 0.12)
	stone_alt_material = _surface_material(Color("#25333e"), "stone", 0.58, 0.10)
	window_material = _emissive_material(Color("#d27a38"), 0.92)
	lantern_material = _emissive_material(Color("#c92f25"), 1.45)
	banner_material = _surface_material(Color("#7f201d"), "cloth", 0.88)
	brass_material = _material(Color("#9d6d32"), 0.38, 0.72)
	earth_material = _surface_material(Color("#2c2418"), "earth", 0.97)
	earth_alt_material = _surface_material(Color("#231d12"), "earth", 0.95)

func _build_environment() -> void:
	var world_environment := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.0, 0.0, 0.0, 0.0)
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

func _build_street() -> void:
	_box(world_root, "StreetBase", Vector3(0.0, -0.18, -25.0), Vector3(9.4, 0.35, 86.0), stone_material)
	_box(world_root, "LeftWalk", Vector3(-5.2, 0.02, -25.0), Vector3(1.0, 0.35, 86.0), stone_alt_material)
	_box(world_root, "RightWalk", Vector3(5.2, 0.02, -25.0), Vector3(1.0, 0.35, 86.0), stone_alt_material)
	_box(world_root, "LeftGround", Vector3(-12.0, -0.18, -25.0), Vector3(13.0, 0.36, 88.0), earth_material)
	_box(world_root, "RightGround", Vector3(12.0, -0.18, -25.0), Vector3(13.0, 0.36, 88.0), earth_alt_material)

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
	_build_house(-1.0, Vector3(-9.70, -0.20, -0.20), 5.10, 7.45, 4.20, 2, 0)

func _build_house(side: float, origin: Vector3, width: float, depth: float, height: float, levels: int, index: int) -> void:
	var house := Node3D.new()
	house.name = "%sHouse%02d" % ["Left" if side < 0.0 else "Right", index]
	house.position = origin
	world_root.add_child(house)
	var wall_material := wall_materials[index % wall_materials.size()]
	_box(house, "StoneFoundation", Vector3(0.0, 0.28, 0.0), Vector3(width * 1.06, 0.56, depth * 1.04), stone_alt_material)
	_box(house, "LowerWall", Vector3(0.0, height * 0.5, 0.0), Vector3(width, height, depth), wall_material)
	_add_timber_frame(house, width, depth, height, side)
	_add_roof(house, Vector3(0.0, height + 0.25, 0.0), width, depth)
	_add_veranda(house, side, width, depth, height)
	_add_brackets(house, side, width, depth, height)

	if levels == 2:
		var upper_width := width * 0.78
		var upper_depth := depth * 0.78
		var upper_height := height * 0.68
		var upper_y := height + upper_height * 0.5 + 0.35
		_box(house, "UpperWall", Vector3(0.0, upper_y, 0.0), Vector3(upper_width, upper_height, upper_depth), wall_material)
		_add_timber_frame(house, upper_width, upper_depth, upper_y + upper_height * 0.5, side, upper_y - upper_height * 0.5)
		_add_roof(house, Vector3(0.0, upper_y + upper_height * 0.5 + 0.22, 0.0), upper_width, upper_depth)
		_add_balcony(house, side, upper_width, upper_depth, upper_y - upper_height * 0.45)
		_add_brackets(house, side, upper_width, upper_depth, upper_y + upper_height * 0.44)

	_add_facade_details(house, side, width, depth, height)
	_add_gable_facade(house, width, depth, height, index)
	_add_banner(house, side, width, depth, height, index)

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
		for strip in 8:
			var x := side * width * (0.065 + float(strip) * 0.058)
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
	for z_end in [-depth * 0.64, depth * 0.64]:
		var cap_mesh := SphereMesh.new()
		cap_mesh.radius = 0.17
		cap_mesh.height = 0.34
		cap_mesh.radial_segments = 10
		cap_mesh.rings = 5
		var cap := MeshInstance3D.new()
		cap.name = "RidgeCap"
		cap.mesh = cap_mesh
		cap.material_override = brass_material
		cap.position = Vector3(0.0, 0.78, z_end)
		roof.add_child(cap)

func _add_facade_details(parent: Node3D, side: float, width: float, depth: float, height: float) -> void:
	var inner_x := -side * width * 0.515
	_box(parent, "Door", Vector3(inner_x, height * 0.38, 0.0), Vector3(0.14, height * 0.72, depth * 0.24), dark_wood_material)
	for z_offset in [-depth * 0.31, depth * 0.31]:
		_box(parent, "Window", Vector3(inner_x - side * 0.015, height * 0.62, z_offset), Vector3(0.12, height * 0.25, depth * 0.18), window_material)
		for bar in [-0.36, -0.12, 0.12, 0.36]:
			_box(parent, "WindowBar", Vector3(inner_x - side * 0.03, height * 0.62 + bar * height * 0.22, z_offset), Vector3(0.14, 0.045, depth * 0.19), dark_wood_material)
		for z_bar in [-0.31, -0.10, 0.10, 0.31]:
			_box(parent, "WindowLattice", Vector3(inner_x - side * 0.035, height * 0.62, z_offset + z_bar * depth * 0.16), Vector3(0.15, height * 0.27, 0.045), dark_wood_material)

func _add_gable_facade(parent: Node3D, width: float, depth: float, height: float, index: int) -> void:
	var front_z := depth * 0.507
	_box(parent, "GableSill", Vector3(0.0, 0.78, front_z), Vector3(width * 0.94, 0.22, 0.16), dark_wood_material)
	_box(parent, "GableMidBeam", Vector3(0.0, height * 0.53, front_z), Vector3(width * 0.94, 0.20, 0.16), wood_material)
	_box(parent, "GableTopBeam", Vector3(0.0, height * 0.90, front_z), Vector3(width * 0.96, 0.24, 0.18), dark_wood_material)
	for x_ratio_value in [-0.42, -0.21, 0.0, 0.21, 0.42]:
		var x_ratio: float = float(x_ratio_value)
		_box(parent, "GablePost", Vector3(width * x_ratio, height * 0.52, front_z), Vector3(0.18, height * 0.80, 0.17), wood_material)
	for x_ratio_value in [-0.29, 0.29]:
		var x_ratio: float = float(x_ratio_value)
		var window_x: float = width * x_ratio
		_box(parent, "GableWindowGlow", Vector3(window_x, height * 0.62, front_z + 0.025), Vector3(width * 0.23, height * 0.29, 0.12), window_material)
		for line in [-0.30, -0.10, 0.10, 0.30]:
			_box(parent, "GableWindowBarH", Vector3(window_x, height * (0.62 + line * 0.25), front_z + 0.07), Vector3(width * 0.25, 0.045, 0.08), dark_wood_material)
			_box(parent, "GableWindowBarV", Vector3(window_x + width * line * 0.18, height * 0.62, front_z + 0.075), Vector3(0.045, height * 0.31, 0.08), dark_wood_material)
	var medallion_mesh := CylinderMesh.new()
	medallion_mesh.top_radius = 0.42
	medallion_mesh.bottom_radius = 0.42
	medallion_mesh.height = 0.12
	medallion_mesh.radial_segments = 18
	var medallion := MeshInstance3D.new()
	medallion.name = "CarvedMedallion"
	medallion.mesh = medallion_mesh
	medallion.material_override = brass_material if index == 0 else dark_wood_material
	medallion.position = Vector3(0.0, height * 0.79, front_z + 0.10)
	medallion.rotation_degrees.x = 90.0
	parent.add_child(medallion)
	for x_ratio_value in [-0.35, 0.35]:
		var x_ratio: float = float(x_ratio_value)
		_box(parent, "DiagonalBrace", Vector3(width * x_ratio, height * 0.29, front_z + 0.04), Vector3(width * 0.28, 0.13, 0.10), brass_material, Vector3(0.0, 0.0, (-1.0 if x_ratio < 0.0 else 1.0) * deg_to_rad(34.0)))

func _add_veranda(parent: Node3D, side: float, width: float, depth: float, height: float) -> void:
	var inner_x := -side * (width * 0.5 + 0.72)
	_box(parent, "VerandaDeck", Vector3(inner_x, 0.64, 0.0), Vector3(1.42, 0.20, depth * 0.92), wood_material)
	for z_offset in [-depth * 0.41, -depth * 0.14, depth * 0.14, depth * 0.41]:
		_box(parent, "VerandaPost", Vector3(inner_x - side * 0.50, height * 0.49, z_offset), Vector3(0.15, height * 0.96, 0.15), dark_wood_material)
		_box(parent, "RailPost", Vector3(inner_x - side * 0.58, 1.12, z_offset), Vector3(0.11, 1.0, 0.11), brass_material)
	_box(parent, "VerandaRail", Vector3(inner_x - side * 0.58, 1.48, 0.0), Vector3(0.10, 0.11, depth * 0.92), brass_material)
	_box(parent, "VerandaCanopy", Vector3(inner_x, height * 0.84, 0.0), Vector3(1.72, 0.14, depth * 1.02), roof_material, Vector3(0.0, 0.0, side * deg_to_rad(8.0)))

func _add_balcony(parent: Node3D, side: float, width: float, depth: float, y: float) -> void:
	var inner_x := -side * (width * 0.5 + 0.58)
	_box(parent, "BalconyDeck", Vector3(inner_x, y, 0.0), Vector3(1.18, 0.20, depth * 0.96), wood_material)
	for z_offset in [-depth * 0.42, -depth * 0.21, 0.0, depth * 0.21, depth * 0.42]:
		_box(parent, "BalconyPicket", Vector3(inner_x - side * 0.48, y + 0.54, z_offset), Vector3(0.09, 0.92, 0.09), brass_material)
	_box(parent, "BalconyRail", Vector3(inner_x - side * 0.48, y + 0.92, 0.0), Vector3(0.11, 0.11, depth * 0.94), brass_material)

func _add_brackets(parent: Node3D, side: float, width: float, depth: float, y: float) -> void:
	var inner_x := -side * (width * 0.5 + 0.22)
	for z_offset in [-depth * 0.38, -depth * 0.19, 0.0, depth * 0.19, depth * 0.38]:
		_box(parent, "BracketA", Vector3(inner_x, y - 0.10, z_offset), Vector3(0.70, 0.16, 0.16), wood_material, Vector3(0.0, 0.0, side * deg_to_rad(22.0)))
		_box(parent, "BracketB", Vector3(inner_x - side * 0.18, y - 0.30, z_offset), Vector3(0.42, 0.12, 0.12), brass_material, Vector3(0.0, 0.0, side * deg_to_rad(-28.0)))

func _add_banner(parent: Node3D, side: float, width: float, depth: float, height: float, index: int) -> void:
	var pivot := Node3D.new()
	pivot.name = "HangingBanner"
	pivot.position = Vector3(-side * (width * 0.53 + 0.18), height * 0.70, depth * (0.12 if index % 2 == 0 else -0.12))
	pivot.set_meta("phase", float(index) * 1.73 + side)
	parent.add_child(pivot)
	_box(pivot, "BannerCloth", Vector3(-side * 0.08, -0.72, 0.0), Vector3(0.08, 1.54, 0.82), banner_material)
	_box(pivot, "BannerRod", Vector3(0.0, 0.08, 0.0), Vector3(0.18, 0.10, 1.08), brass_material)
	banner_nodes.append(pivot)

func _build_lanterns() -> void:
	for row in 5:
		var z := 7.2 - float(row) * 4.9
		var post_x := -5.55
		var post_mesh := CylinderMesh.new()
		post_mesh.top_radius = 0.045
		post_mesh.bottom_radius = 0.065
		post_mesh.height = 3.5
		post_mesh.radial_segments = 8
		var post := MeshInstance3D.new()
		post.name = "RedLanternPost"
		post.mesh = post_mesh
		post.material_override = dark_wood_material
		post.position = Vector3(post_x, 1.75, z)
		world_root.add_child(post)
		_box(world_root, "LanternArm", Vector3(post_x + 0.42, 3.36, z), Vector3(0.86, 0.09, 0.09), dark_wood_material)
		var lantern_mesh := SphereMesh.new()
		lantern_mesh.radius = 0.29
		lantern_mesh.height = 0.76
		lantern_mesh.radial_segments = 16
		lantern_mesh.rings = 8
		var lantern := MeshInstance3D.new()
		lantern.name = "ChineseRedLantern"
		lantern.mesh = lantern_mesh
		lantern.material_override = lantern_material
		lantern.position = Vector3(post_x + 0.74, 2.98, z)
		world_root.add_child(lantern)
		_box(world_root, "LanternTop", lantern.position + Vector3(0.0, 0.39, 0.0), Vector3(0.22, 0.08, 0.22), brass_material)
		_box(world_root, "LanternBottom", lantern.position + Vector3(0.0, -0.39, 0.0), Vector3(0.18, 0.08, 0.18), brass_material)
		var tassel_mesh := CylinderMesh.new()
		tassel_mesh.top_radius = 0.025
		tassel_mesh.bottom_radius = 0.012
		tassel_mesh.height = 0.46
		tassel_mesh.radial_segments = 6
		var tassel := MeshInstance3D.new()
		tassel.name = "LanternTassel"
		tassel.mesh = tassel_mesh
		tassel.material_override = banner_material
		tassel.position = lantern.position + Vector3(0.0, -0.64, 0.0)
		world_root.add_child(tassel)
		if row % 2 == 0:
			var light := OmniLight3D.new()
			light.name = "RedLanternGlow"
			light.position = lantern.position
			light.light_color = Color("#ef3f30")
			light.light_energy = 2.2
			light.omni_range = 7.2
			light.shadow_enabled = false
			world_root.add_child(light)

func _build_fire_braziers() -> void:
	var orange_flame := _emissive_material(Color("#e93d18"), 1.65)
	var gold_flame := _emissive_material(Color("#ff9f32"), 1.85)
	var brazier_positions := [
		Vector3(-4.45, 0.0, 5.6),
		Vector3(4.35, 0.0, -3.8)
	]
	for i in brazier_positions.size():
		var position: Vector3 = brazier_positions[i]
		var pedestal := CylinderMesh.new()
		pedestal.top_radius = 0.33
		pedestal.bottom_radius = 0.48
		pedestal.height = 0.72
		pedestal.radial_segments = 12
		var base := MeshInstance3D.new()
		base.name = "FireBrazierBase"
		base.mesh = pedestal
		base.material_override = brass_material
		base.position = position + Vector3(0.0, 0.36, 0.0)
		world_root.add_child(base)
		var bowl := CylinderMesh.new()
		bowl.top_radius = 0.58
		bowl.bottom_radius = 0.30
		bowl.height = 0.30
		bowl.radial_segments = 16
		var bowl_instance := MeshInstance3D.new()
		bowl_instance.name = "FireBrazierBowl"
		bowl_instance.mesh = bowl
		bowl_instance.material_override = dark_wood_material
		bowl_instance.position = position + Vector3(0.0, 0.82, 0.0)
		world_root.add_child(bowl_instance)
		for lobe_index in 4:
			var flame_mesh := SphereMesh.new()
			flame_mesh.radius = 0.18 + float(lobe_index % 2) * 0.05
			flame_mesh.height = 0.76 + float(lobe_index) * 0.12
			flame_mesh.radial_segments = 10
			flame_mesh.rings = 6
			var flame := MeshInstance3D.new()
			flame.name = "AnimatedFireLobe"
			flame.mesh = flame_mesh
			flame.material_override = gold_flame if lobe_index == 0 else orange_flame
			var offset_x := (float(lobe_index) - 1.5) * 0.14
			var base_y := position.y + 1.16 + float(lobe_index % 2) * 0.13
			flame.position = Vector3(position.x + offset_x, base_y, position.z + (0.10 if lobe_index % 2 == 0 else -0.08))
			flame.rotation_degrees.z = -16.0 + float(lobe_index) * 11.0
			flame.set_meta("phase", float(i) * 2.9 + float(lobe_index) * 1.7)
			flame.set_meta("base_y", base_y)
			flame.set_meta("base_scale", Vector3(0.82, 1.0 + float(lobe_index) * 0.08, 0.82))
			world_root.add_child(flame)
			fire_nodes.append(flame)
		var firelight := OmniLight3D.new()
		firelight.name = "FireGlow"
		firelight.position = position + Vector3(0.0, 1.20, 0.0)
		firelight.light_color = Color("#ff6f32")
		firelight.light_energy = 5.2
		firelight.omni_range = 8.0
		firelight.shadow_enabled = false
		world_root.add_child(firelight)

func _build_clouds() -> void:
	var cloud_specs := [
		Vector4(-18.0, 17.2, -34.0, 0.72),
		Vector4(8.0, 20.0, -45.0, 0.46),
		Vector4(-4.0, 13.8, -25.0, 0.92),
		Vector4(16.0, 8.4, -20.0, 0.58),
		Vector4(-22.0, 5.2, -16.0, 0.38)
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
		cloud_shader_material.set_shader_parameter("opacity", 0.30 - float(i) * 0.028)
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
		sin(elapsed * 0.075) * 0.16,
		4.8 + sin(elapsed * 0.052) * 0.06,
		17.5 + cos(elapsed * 0.038) * 0.08
	)
	camera.position = camera_position
	camera.look_at(Vector3(sin(elapsed * 0.045) * 0.10, 3.1, -24.0), Vector3.UP)
	for banner in banner_nodes:
		var phase := float(banner.get_meta("phase"))
		banner.rotation.z = sin(elapsed * 0.72 + phase) * 0.035
	for flame in fire_nodes:
		var phase := float(flame.get_meta("phase"))
		var base_y := float(flame.get_meta("base_y"))
		var base_scale: Vector3 = flame.get_meta("base_scale")
		var flicker := sin(elapsed * 7.4 + phase)
		flame.position.y = base_y + flicker * 0.045
		flame.scale = base_scale * Vector3(1.0 - flicker * 0.08, 1.0 + flicker * 0.16, 1.0 - flicker * 0.08)

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

func _surface_material(color: Color, pattern: String, roughness: float, metallic: float = 0.0) -> ShaderMaterial:
	var shader := Shader.new()
	var pattern_code := ""
	match pattern:
		"wood":
			pattern_code = """
	float grain = sin(UV.y * 74.0 + sin(UV.x * 19.0) * 2.8) * 0.5 + 0.5;
	float plank = smoothstep(0.47, 0.52, abs(fract(UV.x * 4.0) - 0.5));
	tone = mix(0.70, 1.14, grain * 0.42) * mix(0.72, 1.0, plank);
	bump = (grain - 0.5) * 0.24;
"""
		"tiles":
			pattern_code = """
	vec2 tile_uv = UV * vec2(13.0, 7.0);
	tile_uv.x += floor(tile_uv.y) * 0.5;
	vec2 cell = abs(fract(tile_uv) - 0.5);
	float seam = smoothstep(0.43, 0.49, max(cell.x, cell.y));
	float curve = 1.0 - cell.x * cell.x * 1.7;
	tone = mix(0.43, 1.18 * curve, 1.0 - seam);
	bump = (1.0 - seam) * curve * 0.30 - 0.10;
"""
		"stone":
			pattern_code = """
	vec2 block_uv = UV * vec2(7.0, 11.0);
	block_uv.x += floor(block_uv.y) * 0.5;
	vec2 cell = abs(fract(block_uv) - 0.5);
	float joint = smoothstep(0.42, 0.49, max(cell.x, cell.y));
	float mottled = hash21(floor(block_uv)) * 0.22;
	tone = mix(0.46, 0.90 + mottled, 1.0 - joint);
	bump = (1.0 - joint) * (mottled - 0.08);
"""
		"cloth":
			pattern_code = """
	float weave = sin(UV.x * 210.0) * sin(UV.y * 170.0);
	float fold = sin(UV.x * 16.0 + sin(UV.y * 7.0)) * 0.5 + 0.5;
	tone = 0.72 + fold * 0.34 + weave * 0.035;
	bump = weave * 0.06 + (fold - 0.5) * 0.10;
"""
		"earth":
			pattern_code = """
	vec2 cell = floor(UV * vec2(11.0, 7.0));
	float n = hash21(cell);
	float pebble = hash21(cell + 0.5);
	float rut = smoothstep(0.46, 0.5, abs(fract(UV.y * 5.0) - 0.5));
	tone = 0.58 + n * 0.32 + pebble * 0.12 - rut * 0.18;
	bump = (n - 0.5) * 0.22;
"""
		_:
			pattern_code = """
	vec2 p = UV * 9.0;
	vec2 i = floor(p);
	vec2 f = fract(p);
	f = f * f * (3.0 - 2.0 * f);
	float a = hash21(i);
	float b = hash21(i + vec2(1.0, 0.0));
	float c = hash21(i + vec2(0.0, 1.0));
	float d = hash21(i + vec2(1.0, 1.0));
	float grain = mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
	float stain = sin(UV.y * 13.0 + grain * 2.4) * 0.5 + 0.5;
	float edge_wear = pow(abs(UV.x - 0.5) * 2.0, 3.0) * 0.10;
	tone = 0.78 + grain * 0.17 + stain * 0.10 - edge_wear;
	bump = (grain - 0.5) * 0.08;
"""
	shader.code = """
shader_type spatial;
render_mode diffuse_burley, specular_schlick_ggx;
uniform vec4 base_color : source_color;
uniform float surface_roughness = 0.8;
uniform float surface_metallic = 0.0;
float hash21(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}
void fragment() {
	float tone = 1.0;
	float bump = 0.0;
%s
	ALBEDO = base_color.rgb * tone;
	ROUGHNESS = clamp(surface_roughness - bump * 0.18, 0.18, 1.0);
	METALLIC = surface_metallic;
	NORMAL_MAP = vec3(0.5 + dFdx(bump) * 0.85, 0.5 + dFdy(bump) * 0.85, 1.0);
	NORMAL_MAP_DEPTH = 0.42;
}
""" % pattern_code
	var material := ShaderMaterial.new()
	material.shader = shader
	material.set_shader_parameter("base_color", color)
	material.set_shader_parameter("surface_roughness", roughness)
	material.set_shader_parameter("surface_metallic", metallic)
	return material

func _emissive_material(color: Color, energy: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color.darkened(0.35)
	material.roughness = 0.72
	material.emission_enabled = true
	material.emission = color
	material.emission_energy_multiplier = energy
	return material
