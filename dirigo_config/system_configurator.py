import customtkinter as ctk

from dirigo.config.system_config import SystemMetadata

from dirigo_config.provenance import generated_by_string
from dirigo_config.ui.forms.pydantic_form import build_form_from_model
from dirigo_config.ui.forms.device_card import DeviceCard
from dirigo_config.discovery.devices import discover_kinds_and_groups



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
        # label_text="System Configuration",
        # label_font=ctk.CTkFont(size=16, weight="bold"),
    )
    page.grid(row=0, column=0, sticky="nsew", padx=16, pady=16)
    page.grid_columnconfigure(0, weight=1)

    # Footer (row 1) pinned to bottom
    footer = ctk.CTkFrame(app, corner_radius=12)
    footer.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 16))
    footer.grid_columnconfigure(0, weight=1)

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
        parent      = page,
        model_cls   = SystemMetadata,
        instance    = system_metadata,
    )
    meta_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    # ---------- Devices section ----------
    kind_to_group = discover_kinds_and_groups()

    devices_title = ctk.CTkLabel(page, text="Devices", font=ctk.CTkFont(size=15, weight="bold"))
    devices_title.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 8))

    device_count = 0
    next_row = 3  # first row after the Devices header

    def make_add_row(row: int) -> ctk.CTkFrame:
        """
        Create a row that contains the 'Add Device' button.
        This row is placed where the next device card will appear.
        """
        add_row = ctk.CTkFrame(page, corner_radius=12)
        add_row.grid(row=row, column=0, sticky="ew", padx=12, pady=(0, 10))
        
        # Three columns: left spacer | button | right spacer
        add_row.grid_columnconfigure(0, weight=1)
        add_row.grid_columnconfigure(1, weight=0)
        add_row.grid_columnconfigure(2, weight=1)

        def on_add_clicked() -> None:
            nonlocal device_count, next_row
            device_count += 1

            for child in add_row.winfo_children():
                child.destroy()

            # Insert the actual device card at the same row index
            card = DeviceCard(
                add_row,
                device_number = device_count,
                kind_to_group = kind_to_group,
            )
            card.pack(fill="x", expand=True, padx=0, pady=0)

            # Create the next "Add Device" row just below this card
            next_row = row + 1
            make_add_row(next_row)

        add_btn = ctk.CTkButton(
            add_row,
            text    = "+ Add Device",
            width   = 160,
            command = on_add_clicked,
        )
        add_btn.grid(row=0, column=1, pady=16)

        return add_row

    # Put the first "Add Device" row where the first device card will go
    make_add_row(next_row)

     # ---------- Footer actions ----------
    def on_export_clicked() -> None:
        # TODO: wire to export logic
        print("Export clicked (TODO)")

    export_btn = ctk.CTkButton(
        footer,
        text="Export to TOML…",
        width=160,
        command=on_export_clicked,
    )
    export_btn.grid(row=0, column=1, sticky="e", padx=12, pady=12)


    app.mainloop()



if __name__ == "__main__":
    main()

