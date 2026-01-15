import vtk

class VTKVolumeHelper:
    def __init__(self):
        self.reader_ct = vtk.vtkNIFTIImageReader()
        self.mapper_ct = vtk.vtkSmartVolumeMapper()
        self.volume_ct = vtk.vtkVolume()
        self.property_ct = vtk.vtkVolumeProperty()

        self.reader_seg = vtk.vtkNIFTIImageReader()
        self.mapper_seg = vtk.vtkSmartVolumeMapper()
        self.volume_seg = vtk.vtkVolume()
        self.property_seg = vtk.vtkVolumeProperty()
        self.raw_ct_data = None
        
        # Lưu trữ trạng thái opacity hiện tại
        self.current_liver_opacity = 0.6 

    def load_ct_volume(self, file_path):
        print(f"Loading Base CT: {file_path}")
        self.reader_ct.SetFileName(file_path)
        self.reader_ct.Update()
        self.raw_ct_data = self.reader_ct.GetOutput()

        self.mapper_ct.SetInputConnection(self.reader_ct.GetOutputPort())
        self._setup_transparent_ct_style()
        
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
        self.property_ct.ShadeOn()
        self.property_ct.SetAmbient(0.1) 
        self.property_ct.SetDiffuse(0.9)
        self.property_ct.SetSpecular(0.2) 
        self.property_ct.SetInterpolationTypeToLinear()
        
        opacity = vtk.vtkPiecewiseFunction()
        opacity.AddPoint(-3024, 0.0)
        opacity.AddPoint(-200, 0.0) 
        opacity.AddPoint(-100, 0.005) 
        opacity.AddPoint(40, 0.01)
        opacity.AddPoint(400, 0.1) 
        opacity.AddPoint(3000, 0.1)
        self.property_ct.SetScalarOpacity(opacity)

        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(-1000, 0.0, 0.0, 0.0)
        color.AddRGBPoint(-200,  0.8, 0.5, 0.4)
        color.AddRGBPoint(0,     0.9, 0.6, 0.5)
        color.AddRGBPoint(400,   1.0, 1.0, 0.9)
        self.property_ct.SetColor(color)

    def _setup_segmentation_style(self):
        self.property_seg.ShadeOn() 
        self.property_seg.SetInterpolationTypeToLinear()
        self.property_seg.SetAmbient(0.3) 
        self.property_seg.SetDiffuse(1.0) 
        self.property_seg.SetSpecular(0.2) 
        
        # Sử dụng hàm set_liver_opacity để thiết lập opacity ban đầu
        self.set_liver_opacity(self.current_liver_opacity)
        
        color = vtk.vtkColorTransferFunction()
        color.AddRGBPoint(0.0, 0.0, 0.0, 0.0) 
        color.AddRGBPoint(0.5, 0.0, 1.0, 0.0) # Gan: Xanh
        color.AddRGBPoint(1.4, 0.0, 1.0, 0.0)
        color.AddRGBPoint(1.6, 1.0, 0.0, 0.0) # U: Đỏ
        color.AddRGBPoint(2.5, 1.0, 0.0, 0.0) 
        self.property_seg.SetColor(color)

    def set_liver_opacity(self, opacity_value):
        """
        Điều chỉnh độ trong suốt của Gan (Label 1)
        opacity_value: 0.0 (biến mất) -> 1.0 (đặc)
        """
        self.current_liver_opacity = opacity_value
        
        opacity = vtk.vtkPiecewiseFunction()
        opacity.AddPoint(0.0, 0.0)
        opacity.AddPoint(0.4, 0.0) 
        
        # Label 1: Gan (Range 0.5 -> 1.4)
        opacity.AddPoint(0.5, opacity_value) 
        opacity.AddPoint(1.4, opacity_value)
        
        opacity.AddPoint(1.45, 0.0) 
        opacity.AddPoint(1.55, 0.0)
        
        # Label 2: Khối U (Range 1.6 -> 2.5) -> Luôn hiển thị (1.0)
        opacity.AddPoint(1.6, 1.0)
        opacity.AddPoint(2.5, 1.0)
        
        self.property_seg.SetScalarOpacity(opacity)

    def get_raw_data(self):
        return self.raw_ct_data
    
    def get_segmentation_data(self):
        if self.reader_seg.GetFileName():
            return self.reader_seg.GetOutput()
        return None
        
    def set_opacity_factor(self, value):
        if value <= 0: value = 0.01
        self.property_ct.SetScalarOpacityUnitDistance(1.0 / value)

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