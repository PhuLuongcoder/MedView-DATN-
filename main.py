import tkinter as tk
from tkinter import filedialog, messagebox
import vtk
import os
from backend.volume_renderer import VTKVolumeHelper 
from backend.handler import MPRViewer 

vtk.vtkObject.GlobalWarningDisplayOff()

class MedViewApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MedView Pro - Integrated Workstation")
        self.geometry("1280x720")
        self.configure(bg="#1e1e1e")
        self.iconbitmap(default=None)
        self.backend = VTKVolumeHelper()
        self.mpr_viewer = None 
        self.is_mpr_active = False
        
        self.paned_window = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg="#1e1e1e", sashwidth=4, sashrelief=tk.RAISED)
        self.paned_window.pack(fill=tk.BOTH, expand=True)
        self.frame_left = tk.Frame(self.paned_window, bg="#2d2d2d", width=300)
        self.paned_window.add(self.frame_left, minsize=250)
        self.frame_right = tk.Frame(self.paned_window, bg="black")
        self.paned_window.add(self.frame_right, stretch="always")
        
        self._create_control_panel()
        self._init_vtk_embedded()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_control_panel(self):
        pad_x = 15
        lbl_title = tk.Label(self.frame_left, text="MEDVIEW PRO", fg="#4CAF50", bg="#2d2d2d", font=("Segoe UI", 16, "bold"))
        lbl_title.pack(pady=(20, 30))
        
        # --- DATA GROUP ---
        lbl_grp1 = tk.Label(self.frame_left, text="DATA IMPORT", fg="#888", bg="#2d2d2d", font=("Arial", 9, "bold"))
        lbl_grp1.pack(anchor="w", padx=pad_x)
        btn_load = tk.Button(self.frame_left, text="📂 1. Load CT Volume", 
                             bg="#007ACC", fg="white", font=("Arial", 10), height=2, relief="flat",
                             command=self.action_load_ct)
        btn_load.pack(fill=tk.X, padx=pad_x, pady=5)
        self.btn_overlay = tk.Button(self.frame_left, text="➕ 2. Load Segmentation", 
                             bg="#444", fg="white", font=("Arial", 10), height=2, relief="flat",
                             state="disabled",
                             command=self.action_load_overlay)
        self.btn_overlay.pack(fill=tk.X, padx=pad_x, pady=5)
        tk.Frame(self.frame_left, bg="#444", height=1).pack(fill=tk.X, padx=pad_x, pady=15)
        
        # --- VISUALIZATION GROUP ---
        lbl_grp2 = tk.Label(self.frame_left, text="VISUALIZATION", fg="#888", bg="#2d2d2d", font=("Arial", 9, "bold"))
        lbl_grp2.pack(anchor="w", padx=pad_x)
        self.btn_mpr = tk.Button(self.frame_left, text="🖥️ 3. Toggle MPR (2D/3D)", 
                             bg="#444", fg="white", font=("Arial", 10), height=2, relief="flat",
                             state="disabled",
                             command=self.action_toggle_mpr)
        self.btn_mpr.pack(fill=tk.X, padx=pad_x, pady=5)
        
        # Skin Opacity Slider (CT)
        tk.Label(self.frame_left, text="Skin Opacity (CT):", fg="#ccc", bg="#2d2d2d").pack(anchor="w", padx=pad_x, pady=(10,0))
        self.slider = tk.Scale(self.frame_left, from_=0.1, to=5.0, resolution=0.1, 
                               orient=tk.HORIZONTAL, bg="#2d2d2d", fg="white", 
                               troughcolor="#444", highlightthickness=0, 
                               command=self.action_change_opacity)
        self.slider.set(1.0)
        self.slider.pack(fill=tk.X, padx=pad_x, pady=5)

        # [NEW] Liver Opacity Slider (Segmentation)
        tk.Label(self.frame_left, text="Liver Opacity (Seg):", fg="#ccc", bg="#2d2d2d").pack(anchor="w", padx=pad_x, pady=(10,0))
        self.slider_liver = tk.Scale(self.frame_left, from_=0.0, to=1.0, resolution=0.05, 
                               orient=tk.HORIZONTAL, bg="#2d2d2d", fg="#4CAF50", 
                               troughcolor="#444", highlightthickness=0, 
                               command=self.action_change_liver_opacity)
        self.slider_liver.set(0.6) # Mặc định hiển thị 60%
        self.slider_liver.pack(fill=tk.X, padx=pad_x, pady=5)
        
        tk.Frame(self.frame_left, bg="#444", height=1).pack(fill=tk.X, padx=pad_x, pady=15)
        
        # --- CONTROL GROUP ---
        self.btn_close = tk.Button(self.frame_left, text="🗑️ Close Case (Reset)", 
                             bg="#D32F2F", fg="white", font=("Arial", 10), height=2, relief="flat",
                             state="disabled",
                             command=self.action_close_case)
        self.btn_close.pack(side=tk.BOTTOM, fill=tk.X, padx=pad_x, pady=20)
        self.lbl_status = tk.Label(self.frame_left, text="System Ready", fg="#666", bg="#2d2d2d", wraplength=200)
        self.lbl_status.pack(side=tk.BOTTOM, pady=5)

    def _init_vtk_embedded(self):
        self.vtk_renderer = vtk.vtkRenderer()
        self.vtk_renderer.SetBackground(0.05, 0.05, 0.05) 
        self.vtk_window = vtk.vtkRenderWindow()
        self.vtk_window.AddRenderer(self.vtk_renderer)
        self.vtk_interactor = vtk.vtkRenderWindowInteractor()
        self.vtk_interactor.SetRenderWindow(self.vtk_window)
        self.frame_right.update_idletasks() 
        window_id = self.frame_right.winfo_id()
        handle_str = "_{:x}_p_void".format(window_id)
        self.vtk_window.SetParentId(handle_str) 
        self.vtk_window.Render()
        self.vtk_interactor.Initialize()
        self.frame_right.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        if self.vtk_window:
            self.vtk_window.SetSize(event.width, event.height)
            self.vtk_window.Render()

    def action_load_ct(self):
        file_path = filedialog.askopenfilename(title="Open CT Volume", filetypes=[("NIfTI", "*.nii;*.nii.gz")])
        if not file_path: return
        self.lbl_status.config(text="Loading CT...")
        self.update()
        try:
            vol_ct = self.backend.load_ct_volume(file_path)
            self.vtk_renderer.RemoveAllViewProps()
            self.vtk_renderer.AddVolume(vol_ct)
            self.vtk_renderer.ResetCamera()
            self.btn_overlay.config(state="normal", bg="#E65100")
            self.btn_mpr.config(state="normal", bg="#388E3C")
            self.btn_close.config(state="normal")
            self.lbl_status.config(text=f"Loaded: {os.path.basename(file_path)}")
            self.vtk_window.Render()
            style = vtk.vtkInteractorStyleTrackballCamera()
            self.vtk_interactor.SetInteractorStyle(style)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def action_load_overlay(self):
        file_path = filedialog.askopenfilename(title="Open Segmentation", filetypes=[("NIfTI", "*.nii;*.nii.gz")])
        if not file_path: return
        try:
            vol_seg = self.backend.load_segmentation_overlay(file_path)
            self.vtk_renderer.AddVolume(vol_seg)
            self.vtk_renderer.ResetCamera()
            self.lbl_status.config(text=f"Overlay: {os.path.basename(file_path)}")
            # Reset thanh slider về mặc định
            self.slider_liver.set(0.6)
            self.vtk_window.Render()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def action_change_opacity(self, val):
        self.backend.set_opacity_factor(float(val))
        self.vtk_window.Render()

    # [NEW] Hàm xử lý thay đổi độ mờ gan
    def action_change_liver_opacity(self, val):
        value = float(val)
        # 1. Cập nhật 3D
        self.backend.set_liver_opacity(value)
        
        # 2. Cập nhật 2D (nếu đang bật)
        if self.is_mpr_active and self.mpr_viewer:
            self.mpr_viewer.update_liver_opacity(value)
            
        self.vtk_window.Render()

    def action_toggle_mpr(self):
        try:
            if self.is_mpr_active:
                if self.mpr_viewer:
                    self.mpr_viewer.clear()
                    self.vtk_window.RemoveRenderer(self.mpr_viewer.ren_axial)
                    self.vtk_window.RemoveRenderer(self.mpr_viewer.ren_coronal)
                    self.vtk_window.RemoveRenderer(self.mpr_viewer.ren_sagittal)
                    self.mpr_viewer = None
                self.vtk_renderer.SetViewport(0, 0, 1, 1)
                self.btn_mpr.config(text="🖥️ 3. Toggle MPR (2D/3D)", bg="#444")
                self.is_mpr_active = False
                self.vtk_window.Render()
                style = vtk.vtkInteractorStyleTrackballCamera()
                self.vtk_interactor.SetInteractorStyle(style)
            else:
                raw_ct = self.backend.get_raw_data()
                raw_seg = self.backend.get_segmentation_data()
                if not raw_ct:
                    messagebox.showwarning("Warning", "Please load CT data first.")
                    return
                # Truyền liver_opacity hiện tại vào viewer để đồng bộ
                current_liver_opacity = self.slider_liver.get()
                self.mpr_viewer = MPRViewer(self.vtk_window, self.vtk_renderer, raw_ct, raw_seg, initial_opacity=current_liver_opacity)
                self.btn_mpr.config(text="❌ Return to 3D Only", bg="#E65100")
                self.is_mpr_active = True
                self.vtk_window.Render()
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            messagebox.showerror("MPR Error", str(e))

    def action_close_case(self):
        if not messagebox.askyesno("Confirm", "Close current case and reset all data?"):
            return
        try:
            if self.is_mpr_active:
                self.action_toggle_mpr()
            self.vtk_renderer.RemoveAllViewProps()
            self.vtk_window.Render()
            self.backend.reset()
            self.btn_overlay.config(state="disabled", bg="#444")
            self.btn_mpr.config(state="disabled", bg="#444", text="🖥️ 3. Toggle MPR (2D/3D)")
            self.btn_close.config(state="disabled")
            self.slider.set(1.0)
            self.slider_liver.set(0.6)
            self.lbl_status.config(text="System Ready")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def on_close(self):
        self.vtk_interactor.TerminateApp()
        self.destroy()

if __name__ == "__main__":
    app = MedViewApp()
    app.mainloop()