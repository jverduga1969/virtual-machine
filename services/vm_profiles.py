from services.host_system_info import get_host_info

def get_vm_profiles():
    """
    Calcula los perfiles de VM basados en el hardware real del Host.
    Devuelve una lista de diccionarios.
    """
    host = get_host_info()
    host_cores = host.get("cpu_logical", 4)
    host_ram_mb = host.get("ram_total_kb", 8192000) // 1024  # Convertir a MB
    
    # Dejamos siempre al menos 1 núcleo y 2GB de RAM para el Host
    max_cores = max(1, host_cores - 1)
    max_ram_mb = max(1024, host_ram_mb - 2048)

    # Perfil 1: Ligera (Hogar básico)
    p_light = {
        "id": "light",
        "name": "Ligera",
        "desc": "Navegación, ofimática",
        "icon": "🌐",
        "cores": min(2, max_cores),
        "ram": min(2048, max_ram_mb),
        "disk_size": "20G",
        "firmware_idx": 0,      # BIOS
        "chipset_idx": 0,       # i440FX
        "graphics_idx": 0,      # VirtIO 2D
        "secure_boot": False,
        "tpm": False,
        "platform": "GNU / Linux",
        "os": "Linux Mint",
    }

    # Perfil 2: Hogar
    p_home = {
        "id": "home",
        "name": "Hogar",
        "desc": "Uso general diario",
        "icon": "🏠",
        "cores": min(4, max_cores),
        "ram": min(4096, max_ram_mb),
        "disk_size": "40G",
        "firmware_idx": 1,      # UEFI
        "chipset_idx": 1,       # Q35
        "graphics_idx": 0,      # VirtIO 2D
        "secure_boot": False,
        "tpm": False,
        "platform": "Microsoft Windows",
        "os": "Windows 10",
    }

    # Perfil 3: Desarrollo
    p_dev = {
        "id": "dev",
        "name": "Desarrollo",
        "desc": "Programación, IDEs",
        "icon": "💻",
        "cores": min(6, max_cores),
        "ram": min(8192, max_ram_mb),
        "disk_size": "80G",
        "firmware_idx": 1,      # UEFI
        "chipset_idx": 1,       # Q35
        "graphics_idx": 2,      # VirtIO + VirGL 3D
        "secure_boot": False,
        "tpm": False,
        "platform": "GNU / Linux",
        "os": "Ubuntu",
    }

    # Perfil 4: Juegos
    p_gaming = {
        "id": "gaming",
        "name": "Juegos",
        "desc": "Gráficos 3D, rendimiento",
        "icon": "🎮",
        "cores": min(8, max_cores),
        "ram": min(16384, max_ram_mb),
        "disk_size": "120G",
        "firmware_idx": 1,      # UEFI
        "chipset_idx": 1,       # Q35
        "graphics_idx": 3,      # VirtIO + Venus (Vulkan)
        "secure_boot": True,
        "tpm": True,
        "platform": "Microsoft Windows",
        "os": "Windows 11",
    }

    return [p_home, p_dev, p_gaming, p_light]