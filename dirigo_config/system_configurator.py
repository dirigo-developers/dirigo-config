# dirigo_config/app.py
from __future__ import annotations

import customtkinter as ctk

from dirigo.config.system_config import SystemMetadata

from dirigo_config.provenance import generated_by_string
from dirigo_config.ui.forms.pydantic_form import build_form_from_model



def main() -> None:
    ctk.set_appearance_mode("Dark")  # "Light", "Dark", or "System"
    ctk.set_default_color_theme("blue")

    app = ctk.CTk()
    app.title("Dirigo System Configurator")
    app.geometry("900x650")
    app.minsize(700, 450)

    app.grid_rowconfigure(0, weight=1)
    app.grid_columnconfigure(0, weight=1)

    page = ctk.CTkScrollableFrame(
        master=app,
        corner_radius=12,
        label_text="System Configuration",
        label_font=ctk.CTkFont(size=16, weight="bold"),
    )
    page.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
    page.grid_columnconfigure(0, weight=1)

    # -------- System Metadata section --------
    meta_title = ctk.CTkLabel(
        page,
        text="System Metadata",
        font=ctk.CTkFont(size=15, weight="bold"),
    )
    meta_title.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 6))

    # Create an instance with configurator provenance injected
    system_metadata = SystemMetadata(generated_by=generated_by_string())

    meta_frame, meta_getters, _ = build_form_from_model(
        parent=page,
        model_cls=SystemMetadata,
        instance=system_metadata,
    )
    meta_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    def dump_metadata():
        values = {k: get() for k, get in meta_getters.items()}
        model = SystemMetadata(**values, generated_by=generated_by_string())  # validation
        print(model.model_dump())

    dump_btn = ctk.CTkButton(page, text="Print metadata dict (debug)", command=dump_metadata)
    dump_btn.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 16))

    app.mainloop()



if __name__ == "__main__":
    main()

