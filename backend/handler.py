import vtk
class MPRInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, parent=None):
        self.parent = parent
        self.AddObserver("MouseWheelForwardEvent", self.OnMouseWheelForward)
        self.AddObserver("MouseWheelBackwardEvent", self.OnMouseWheelBackward)
        self.AddObserver("LeftButtonPressEvent", self.OnLeftButtonDown)

    def _get_target(self):
        if not self.parent: return None, None, None
        x, y = self.GetInteractor().GetEventPosition()
        renderer = self.GetInteractor().FindPokedRenderer(x, y)
        if renderer in self.parent.renderer_map:
            data = self.parent.renderer_map[renderer]
            return renderer, data["ct"], data["seg"]
        return None, None, None

    def OnMouseWheelForward(self, obj, event):
        renderer, ct_widget, seg_widget = self._get_target()
        if ct_widget:
            self._update_slice(renderer, ct_widget, seg_widget, 1)
            return 
        super().OnMouseWheelForward()

    def OnMouseWheelBackward(self, obj, event):
        renderer, ct_widget, seg_widget = self._get_target()
        if ct_widget:
            self._update_slice(renderer, ct_widget, seg_widget, -1)
            return 
        super().OnMouseWheelBackward()

    def _update_slice(self, renderer, ct_widget, seg_widget, direction):
        current = ct_widget.GetSliceIndex()
        axis = ct_widget.GetPlaneOrientation()
        max_slice = ct_widget.GetInput().GetDimensions()[axis] - 1
        step = 10 if self.GetInteractor().GetShiftKey() else 1
        if direction > 0:
            new_slice = min(current + step, max_slice)
        else:
            new_slice = max(current - step, 0)
        ct_widget.SetSliceIndex(new_slice)
        if seg_widget:
            seg_widget.SetSliceIndex(new_slice)
            ct_widget.InvokeEvent("InteractionEvent")
        renderer.ResetCameraClippingRange()
        self.GetInteractor().Render()

    def OnLeftButtonDown(self, obj, event):
        renderer, ct_widget, _ = self._get_target()
        if ct_widget:
            pass 
        else:
            super().OnLeftButtonDown()

class MPRViewer:
    def __init__(self, vtk_window, vtk_renderer_3d, ct_data, seg_data=None, initial_opacity=0.6):
        self.window = vtk_window
        self.ct_data = ct_data
        self.seg_data = seg_data 
        self.current_liver_opacity = initial_opacity
        self.seg_lut = None
        self.ren_axial = vtk.vtkRenderer()
        self.ren_coronal = vtk.vtkRenderer()
        self.ren_sagittal = vtk.vtkRenderer()
        self.ren_3d = vtk_renderer_3d 
        self.ct_widgets = [] 
        self.seg_widgets = []
        self.renderer_map = {} 
        self._setup_viewports()
        self._setup_planes()
        style = MPRInteractorStyle(parent=self)
        self.window.GetInteractor().SetInteractorStyle(style)

    def _setup_viewports(self):
        GAP = 0.002
        HALF = 0.5
        self.ren_axial.SetViewport(0.0, HALF + GAP, HALF - GAP, 1.0)
        self.ren_axial.SetBackground(0.1, 0.1, 0.1)
        self.window.AddRenderer(self.ren_axial)
        self.ren_coronal.SetViewport(HALF + GAP, HALF + GAP, 1.0, 1.0)
        self.ren_coronal.SetBackground(0.1, 0.1, 0.1)
        self.window.AddRenderer(self.ren_coronal)
        self.ren_sagittal.SetViewport(0.0, 0.0, HALF - GAP, HALF - GAP)
        self.ren_sagittal.SetBackground(0.1, 0.1, 0.1)
        self.window.AddRenderer(self.ren_sagittal)
        self.ren_3d.SetViewport(HALF + GAP, 0.0, 1.0, HALF - GAP)

    def _get_dynamic_lut(self):
        if not self.seg_data: return None
        scalar_range = self.seg_data.GetScalarRange()
        max_val = scalar_range[1]
        
        self.seg_lut = vtk.vtkLookupTable()
        
        if max_val <= 1.0:
            self.seg_lut.SetNumberOfTableValues(2)
            self.seg_lut.SetRange(0, 1)
            self.seg_lut.Build()
            self.seg_lut.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)
            self.seg_lut.SetTableValue(1, 1.0, 0.8, 0.0, self.current_liver_opacity)
        else:
            self.seg_lut.SetNumberOfTableValues(3)
            self.seg_lut.SetRange(0, 2)
            self.seg_lut.Build()
            self.seg_lut.SetTableValue(0, 0.0, 0.0, 0.0, 0.0)
            self.seg_lut.SetTableValue(1, 0.0, 1.0, 0.0, self.current_liver_opacity)
            self.seg_lut.SetTableValue(2, 1.0, 0.0, 0.0, 0.6)
        return self.seg_lut

    def update_liver_opacity(self, opacity):
        self.current_liver_opacity = opacity
        if self.seg_lut:
            color = [0.0, 0.0, 0.0, 0.0]
            self.seg_lut.GetTableValue(1, color)
            self.seg_lut.SetTableValue(1, color[0], color[1], color[2], opacity)
            self.window.Render()

    def _setup_planes(self):
        interactor = self.window.GetInteractor()
        if not interactor: return
        picker = vtk.vtkCellPicker()
        picker.SetTolerance(0.005)
        interactor.SetPicker(picker)
        planes_config = [
            (2, self.ren_axial,    (1, 0, 0), "Axial"),
            (1, self.ren_coronal,  (0, 1, 0), "Coronal"),
            (0, self.ren_sagittal, (0, 0, 1), "Sagittal")
        ]
        ct_dims = self.ct_data.GetDimensions()
        bounds = self.ct_data.GetBounds()
        center = self.ct_data.GetCenter()
        max_dim = max(bounds[1]-bounds[0], bounds[3]-bounds[2], bounds[5]-bounds[4])
        cam_distance = max_dim * 1.5
        seg_dims = self.seg_data.GetDimensions() if self.seg_data else None
        seg_lut = self._get_dynamic_lut()
        for axis, renderer, color, name in planes_config:
            try:
                plane_ct = vtk.vtkImagePlaneWidget()
                plane_ct.SetInteractor(interactor)
                plane_ct.SetInputData(self.ct_data)
                plane_ct.SetPlaneOrientation(axis)
                plane_ct.SetSliceIndex(ct_dims[axis] // 2)
                plane_ct.GetPlaneProperty().SetColor(color)
                plane_ct.DisplayTextOn()
                plane_ct.SetDefaultRenderer(renderer)
                plane_ct.On()
                self.ct_widgets.append(plane_ct)
                plane_seg = None
                
                if self.seg_data and seg_lut:
                    plane_seg = vtk.vtkImagePlaneWidget()
                    plane_seg.SetInteractor(interactor)
                    plane_seg.SetInputData(self.seg_data)
                    plane_seg.SetPlaneOrientation(axis)
                    safe_slice = min(plane_ct.GetSliceIndex(), seg_dims[axis] - 1)
                    plane_seg.SetSliceIndex(safe_slice)
                    plane_seg.SetLookupTable(seg_lut)
                    
                    plane_seg.SetUserControlledLookupTable(True)
                    plane_seg.TextureVisibilityOn() 
                    plane_seg.TextureInterpolateOff()
                    
                    plane_seg.GetPlaneProperty().SetOpacity(0.0) 
                    plane_seg.GetPlaneProperty().SetColor(0.0, 0.0, 0.0)
                    
                    plane_seg.DisplayTextOff()
                    plane_seg.SetDefaultRenderer(renderer)
                    plane_seg.On() 
                    plane_seg.InteractionOff()
                    self.seg_widgets.append(plane_seg)
                    
                    def hard_sync_geometry(obj, event):
                        if plane_seg:
                            idx = obj.GetSliceIndex()
                            if 0 <= idx < seg_dims[axis]:
                                plane_seg.SetSliceIndex(idx)
                            plane_seg.UpdatePlacement()
                            o = plane_seg.GetOrigin()
                            p1 = plane_seg.GetPoint1()
                            p2 = plane_seg.GetPoint2()
                            normal = plane_seg.GetNormal()
                            epsilon = 0.1 
                            new_o = (o[0] + normal[0]*epsilon, o[1] + normal[1]*epsilon, o[2] + normal[2]*epsilon)
                            new_p1 = (p1[0] + normal[0]*epsilon, p1[1] + normal[1]*epsilon, p1[2] + normal[2]*epsilon)
                            new_p2 = (p2[0] + normal[0]*epsilon, p2[1] + normal[1]*epsilon, p2[2] + normal[2]*epsilon)
                            plane_seg.SetOrigin(new_o)
                            plane_seg.SetPoint1(new_p1)
                            plane_seg.SetPoint2(new_p2)
                            renderer.ResetCameraClippingRange()
                            
                    plane_ct.AddObserver("InteractionEvent", hard_sync_geometry)
                    hard_sync_geometry(plane_ct, None)
                    
                self.renderer_map[renderer] = {"ct": plane_ct, "seg": plane_seg}
                cam = renderer.GetActiveCamera()
                cam.SetParallelProjection(True)
                if axis == 2:   
                    cam.SetPosition(center[0], center[1], center[2] + cam_distance)
                    cam.SetViewUp(0, 1, 0)
                elif axis == 1: 
                    cam.SetPosition(center[0], center[1] - cam_distance, center[2])
                    cam.SetViewUp(0, 0, 1) 
                elif axis == 0: 
                    cam.SetPosition(center[0] + cam_distance, center[1], center[2])
                    cam.SetViewUp(0, 0, 1) 
                cam.SetFocalPoint(center[0], center[1], center[2])
                renderer.ResetCamera()
            except Exception as e:
                print(f"Lỗi tạo khung {name}: {e}")

    def clear(self):
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.window.GetInteractor().SetInteractorStyle(style)
        for w in self.ct_widgets: w.Off()
        for w in self.seg_widgets: w.Off()
        self.ct_widgets.clear()
        self.seg_widgets.clear()
        self.renderer_map.clear()