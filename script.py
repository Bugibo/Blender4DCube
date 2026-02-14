import bpy
from mathutils import Vector
import math

# --------------------------------------------------
# Функция обновления тессеракта (при изменении свойств)
# --------------------------------------------------
def update_tesseract(self, context):
    obj = self
    
    # Читаем параметры
    viewer_dist = getattr(obj, "viewer_distance", 3.0)
    w_shift     = getattr(obj, "w_shift", 0.0)
    ax = getattr(obj, "angle_xw", 0.0)
    ay = getattr(obj, "angle_yw", 0.0)
    az = getattr(obj, "angle_zw", 0.0)
    
    # 16 вершин 4D гиперкуба (порядок фиксирован!)
    verts4d = [[x, y, z, w] for x in [-1,1] for y in [-1,1] for z in [-1,1] for w in [-1,1]]
    
    # Предвычисляем sin/cos
    cax, sax = math.cos(ax), math.sin(ax)
    cay, say = math.cos(ay), math.sin(ay)
    caz, saz = math.cos(az), math.sin(az)
    
    proj_verts = []
    
    for p in verts4d:
        x, y, z, w = p
        
        # Вращение XW
        nx = x * cax - w * sax
        nw = x * sax + w * cax
        x, w = nx, nw
        
        # Вращение YW
        ny = y * cay - w * say
        nw = y * say + w * cay
        y, w = ny, nw
        
        # Вращение ZW
        nz = z * caz - w * saz
        nw = z * saz + w * caz
        z, w = nz, nw
        
        # Сдвиг по W
        w += w_shift
        
        # Стереографическая проекция
        denom = viewer_dist - w
        if abs(denom) < 0.001:
            scale = 1000.0  # далеко → не делим на почти ноль
        else:
            scale = viewer_dist / denom
            
        proj_verts.append(Vector((x * scale, y * scale, z * scale)))
    
    # --------------------------------------------------
    # 24 грани (квадрата) тессеракта — фиксированный список
    # --------------------------------------------------
    faces = [
        # w = -1 (передний куб)
        [0, 1, 3, 2], [0, 1, 5, 4], [0, 4, 6, 2], [1, 5, 7, 3],
        [2, 3, 7, 6], [4, 5, 7, 6],
        # w = +1 (задний куб)
        [8, 9,11,10], [8, 9,13,12], [8,12,14,10], [9,13,15,11],
        [10,11,15,14], [12,13,15,14],
        # Соединяющие грани (между кубами)
        [0, 1, 9, 8], [2, 3,11,10], [4, 5,13,12], [6, 7,15,14],
        [0, 2,10, 8], [1, 3,11, 9], [4, 6,14,12], [5, 7,15,13],
        [0, 4,12, 8], [1, 5,13, 9], [2, 6,14,10], [3, 7,15,11]
    ]
    
    # Обновляем меш
    if obj.data:
        mesh = obj.data
        mesh.clear_geometry()
        mesh.from_pydata(proj_verts, [], faces)  # edges = [] → Blender сам построит
        mesh.update()
        
        # Опционально: нормали и smooth
        mesh.calc_normals_split()
        # bpy.ops.object.shade_smooth()  # можно раскомментировать, но лучше в интерфейсе


# --------------------------------------------------
# Регистрация свойств на объектах
# --------------------------------------------------
props = [
    ("viewer_distance", 3.0, "Dist W", 0.1, 20.0),
    ("w_shift",         0.0, "Shift W", -10.0, 10.0),
    ("angle_xw",        0.0, "Rot XW", -6.28, 6.28),
    ("angle_yw",        0.0, "Rot YW", -6.28, 6.28),
    ("angle_zw",        0.0, "Rot ZW", -6.28, 6.28),
]

for name, default, desc, vmin, vmax in props:
    setattr(bpy.types.Object, name, bpy.props.FloatProperty(
        name=desc,
        default=default,
        min=vmin, max=vmax,
        update=update_tesseract
    ))


# --------------------------------------------------
# Применяем к активному объекту (если это меш)
# --------------------------------------------------
obj = bpy.context.active_object

if obj and obj.type == 'MESH':
    print(f"Превращаем объект '{obj.name}' в проекцию тессеракта...")
    
    obj["is_tesseract"] = True
    
    # Сбрасываем → это вызовет update_tesseract автоматически
    obj.viewer_distance = 3.0
    obj.w_shift = 0.0
    obj.angle_xw = 0.0
    obj.angle_yw = 0.0
    obj.angle_zw = 0.0
    
    # На всякий случай принудительно
    update_tesseract(obj, bpy.context)
    
    # Делаем объект smooth (красивее выглядит)
    bpy.ops.object.shade_smooth()
    
else:
    print("Выдели MESH-объект (например куб) перед запуском скрипта!")


# --------------------------------------------------
# Панель в N-панели (в 3D Viewport → вкладка Tesseract)
# --------------------------------------------------
class TesseractPanel(bpy.types.Panel):
    bl_label = "Tesseract 4D Controls"
    bl_idname = "OBJECT_PT_tesseract"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Tesseract"
    
    @classmethod
    def poll(cls, context):
        return context.object and context.object.get("is_tesseract")
    
    def draw(self, context):
        layout = self.layout
        obj = context.object
        
        col = layout.column(align=True)
        col.prop(obj, "viewer_distance")
        col.prop(obj, "w_shift")
        col.separator()
        col.prop(obj, "angle_xw")
        col.prop(obj, "angle_yw")
        col.prop(obj, "angle_zw")


# Регистрируем панель (с защитой от повторной регистрации)
try:
    bpy.utils.unregister_class(TesseractPanel)
except:
    pass

bpy.utils.register_class(TesseractPanel)

print("Скрипт тессеракта загружен. Управление в боковой панели (N → Tesseract)")
