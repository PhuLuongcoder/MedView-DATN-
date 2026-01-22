import vtk

class VTKVolumeHelper:
    def __init__(self):
    # Khoi tao cac dau doc cho volume
        self.reader_ct = vtk.vtkNIFTIImageReader() # Dau doc file .nii/.nii.gz
        self.mapper_ct = vtk.vtkSmartVolumeMapper() # Bo chuyen doi de tao hinh khoi
        self.volume_ct = vtk.vtkVolume() # Khung chua ket qua
        self.property_ct = vtk.vtkVolumeProperty() # Chua cac thuoc tinh nhu: Mau sac, do trong suot, anh sang,...
    # Khoi tao cac dau doc cho segmentaion
        self.reader_seg = vtk.vtkNIFTIImageReader()
        self.mapper_seg = vtk.vtkSmartVolumeMapper()
        self.volume_seg = vtk.vtkVolume()
        self.property_seg = vtk.vtkVolumeProperty()
        self.raw_ct_data = None # Bien tam de luu du lieu tho
        self.current_liver_opacity = 0.6 # Luu tru gia tri opacity hien tai cua gan

    def load_ct_volume(self, file_path):
        print(f"Loading Base CT: {file_path}")
        self.reader_ct.SetFileName(file_path)
        self.reader_ct.Update() # Ra lenh cho VTK doc file .nii vao RAM
        self.raw_ct_data = self.reader_ct.GetOutput() # Luu ban goc du lieu de hien thi 2D
        self.mapper_ct.SetInputConnection(self.reader_ct.GetOutputPort()) # Chuyen giao du lieu tu Reader -> Mapper
        self._setup_transparent_ct_style() # Ham cai dat giao dien hien thi Mau sac/Do trong
    # Gan Mapper va Property vao Volume
        self.volume_ct.SetMapper(self.mapper_ct)
        self.volume_ct.SetProperty(self.property_ct)
        return self.volume_ct

    def load_segmentation_overlay(self, file_path):
        print(f"Loading Overlay: {file_path}")
        self.reader_seg.SetFileName(file_path)
        self.reader_seg.Update()
        self.mapper_seg.SetInputConnection(self.reader_seg.GetOutputPort())
        self._setup_segmentation_style()        
        self.volume_seg.SetMapper(self.mapper_seg)
        self.volume_seg.SetProperty(self.property_seg)
        return self.volume_seg

    def _setup_transparent_ct_style(self):
        self.property_ct.ShadeOn() # Bat do bong
        self.property_ct.SetAmbient(0.1) # Anh sang nen
        self.property_ct.SetDiffuse(0.9) # Do khuech tan - anh sang tan ra be mat
        self.property_ct.SetSpecular(0.2) # Do bong loang
        self.property_ct.SetInterpolationTypeToLinear() # Lam min tranh bi vo pixel
    # Cau hinh do trong suot theo thang do Hounsfield-HU
        opacity = vtk.vtkPiecewiseFunction()
        opacity.AddPoint(-3024, 0.0) # Gia tri san -> Tang hinh
        opacity.AddPoint(-200, 0.0) # Khong khi/mo -> Tang hinh 
        opacity.AddPoint(-100, 0.005) # Mo mem -> Hien thi mo
        opacity.AddPoint(40, 0.01) # Co/mau -> Hien ro hon
        opacity.AddPoint(400, 0.1) # Xuong -> Hien ro rang
        opacity.AddPoint(3000, 0.1) # May moc -> Hien ro rang
        self.property_ct.SetScalarOpacity(opacity)
    # Cau hinh mau sac cho tung khoang gia tri HU
        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(-1000, 0.0, 0.0, 0.0) # Khong khi -> Mau den
        color.AddRGBPoint(-200,  0.8, 0.5, 0.4) # Mo mem -> Mau da nguoi
        color.AddRGBPoint(0,     0.9, 0.6, 0.5) # Mau/dich -> Mau do nhat
        color.AddRGBPoint(400,   1.0, 1.0, 0.9) # Xuong -> Mau trang nga
        self.property_ct.SetColor(color)

    def _setup_segmentation_style(self):
        self.property_seg.ShadeOn() 
        self.property_seg.SetInterpolationTypeToLinear()
        self.property_seg.SetAmbient(0.3) 
        self.property_seg.SetDiffuse(1.0) 
        self.property_seg.SetSpecular(0.2) 
        self.set_liver_opacity(self.current_liver_opacity)
    # Set-up bang mau cho nhan (Gan va U)
        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(0.0, 0.0, 0.0, 0.0)
    # Dat gia tri tu 0.5 -> 1.4 de bao quanh 1.0 sau khi noi suy 
        color.AddRGBPoint(0.5, 0.0, 1.0, 0.0)
        color.AddRGBPoint(1.4, 0.0, 1.0, 0.0)
    # Tuong tu voi khoi U, gia tri tu 1.6 -> 2.5
        color.AddRGBPoint(1.6, 1.0, 0.0, 0.0)
        color.AddRGBPoint(2.5, 1.0, 0.0, 0.0) 
        self.property_seg.SetColor(color)

    def set_liver_opacity(self, opacity_value):
        self.current_liver_opacity = opacity_value
    # Vung nen luon luon tang hinh
        opacity = vtk.vtkPiecewiseFunction()
        opacity.AddPoint(0.0, 0.0)
        opacity.AddPoint(0.4, 0.0) 
    # Label 1: Gan (Range 0.5 -> 1.4)
        opacity.AddPoint(0.5, opacity_value) 
        opacity.AddPoint(1.4, opacity_value)
    # Vung chuyen tiep giua gan va u
        opacity.AddPoint(1.45, 0.0) 
        opacity.AddPoint(1.55, 0.0)
    # Label 2: Khoi U (Range 1.6 -> 2.5) -> Luon hien thi
        opacity.AddPoint(1.6, 1.0)
        opacity.AddPoint(2.5, 1.0)
        self.property_seg.SetScalarOpacity(opacity)

    def get_raw_data(self): # Ham tra ve du lieu tho tu file CT de hien thi 3 lat cat 2D
        return self.raw_ct_data
    
    def get_segmentation_data(self):
        if self.reader_seg.GetFileName():
            return self.reader_seg.GetOutput()
        return None
        
    def set_opacity_factor(self, value):
        if value <= 0: value = 0.01
        self.property_ct.SetScalarOpacityUnitDistance(1.0 / value)

    def set_ct_visiblility(self, is_visible):
        if self.volume_ct:
            self.volume_ct.SetVisibility(is_visible)

    def set_seg_visiblility(self, is_visible):
        if self.volume_seg:
            self.volume_seg.SetVisibility(is_visible)

    def reset(self):
        self.reader_ct = vtk.vtkNIFTIImageReader()
        self.mapper_ct = vtk.vtkSmartVolumeMapper()
        self.volume_ct = vtk.vtkVolume()
        self.property_ct = vtk.vtkVolumeProperty()
        self.reader_seg = vtk.vtkNIFTIImageReader()
        self.mapper_seg = vtk.vtkSmartVolumeMapper()
        self.volume_seg = vtk.vtkVolume()
        self.property_seg = vtk.vtkVolumeProperty()    
        self.raw_ct_data = None
        self.current_liver_opacity = 0.6
        print("Backend đã được Reset sạch sẽ.")