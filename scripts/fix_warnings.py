from pathlib import Path
import re
import sys 

root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()

# 1) CS0659 en Quaver.API (TimingGroup y ScrollGroup)
tg = root / "Quaver.API" / "Quaver.API" / "Maps" / "Structures" / "TimingGroup.cs"
if tg.is_file():
    t = tg.read_text(encoding="utf-8-sig")
    if "GetHashCode()" not in t:
        t = t.replace(
            "            return Equals((TimingGroup)obj);\n        }",
            "            return Equals((TimingGroup)obj);\n        }\n\n"
            "        public override int GetHashCode()\n"
            "        {\n"
            "            unchecked\n"
            "            {\n"
            "                return ((ColorRgb != null ? ColorRgb.GetHashCode() : 0) * 397) ^ Hidden.GetHashCode();\n"
            "            }\n"
            "        }",
        )
        tg.write_text(t, encoding="utf-8")

sg = root / "Quaver.API" / "Quaver.API" / "Maps" / "Structures" / "ScrollGroup.cs"
if sg.is_file():
    t = sg.read_text(encoding="utf-8-sig")
    if "GetHashCode()" not in t:
        t = t.replace(
            "            return Equals((ScrollGroup)obj);\n        }",
            "            return Equals((ScrollGroup)obj);\n        }\n\n"
            "        public override int GetHashCode()\n"
            "        {\n"
            "            unchecked\n"
            "            {\n"
            "                var hashCode = base.GetHashCode();\n"
            "                hashCode = (hashCode * 397) ^ InitialScrollVelocity.GetHashCode();\n"
            "                if (ScrollVelocities != null)\n"
            "                    foreach (var sv in ScrollVelocities)\n"
            "                        hashCode = (hashCode * 397) ^ SliderVelocityInfo.ByValueComparer.GetHashCode(sv);\n"
            "                if (ScrollSpeedFactors != null)\n"
            "                    foreach (var ssf in ScrollSpeedFactors)\n"
            "                        hashCode = (hashCode * 397) ^ ScrollSpeedFactorInfo.ByValueComparer.GetHashCode(ssf);\n"
            "                return hashCode;\n"
            "            }\n"
            "        }",
        )
        sg.write_text(t, encoding="utf-8")

# 2) Silenciar warnings de submódulos (CS0108, CS0168, CS0169, CS0659, CS1570, CS1572, CS1574)
extra = ";CS0105;CS0108;CS0114;CS0168;CS0169;CS0659;CS1570;CS1572;CS1574;CS8625"
for rel in (
    "Quaver.API/Quaver.API/Quaver.API.csproj",
    "Wobble/Wobble/Wobble.csproj",
    "Wobble/Wobble.Extended/Wobble.Extended.csproj",
    "Quaver.Shared/Quaver.Shared.csproj",
    "android-head/QuaverAndroid.csproj",
):
    p = root / rel
    if not p.is_file():
        continue
    txt = p.read_text(encoding="utf-8-sig")
    if "CS1570" not in txt and "</NoWarn>" in txt:
        txt = txt.replace("</NoWarn>", f"{extra}</NoWarn>")
        p.write_text(txt, encoding="utf-8")

# 3) ConfigManager & StructuredConfigManager: evitar deadlock en hilo UI + ruta valida de SteamWorkshopDirectory en Android
cm = root / "Quaver.Shared" / "Config" / "ConfigManager.cs"
if cm.is_file():
    ct = cm.read_text(encoding="utf-8-sig")
    cm_changed = False
    if "internal static async Task WriteConfigFileAsync()" in ct:
        ct = ct.replace(
            "internal static async Task WriteConfigFileAsync()",
            "internal static Task WriteConfigFileAsync()",
        )
        ct = ct.replace(
            "await sw.WriteLineAsync(sb.ToString());",
            "sw.WriteLine(sb.ToString());",
        )
        ct = ct.replace(
            "            LastWrite = GameBase.Game?.TimeRunning ?? -1;\n        }",
            "            LastWrite = GameBase.Game?.TimeRunning ?? -1;\n            return Task.CompletedTask;\n        }",
        )
        cm_changed = True
    old_ws = '_steamWorkshopDirectory = $"{GameDirectory.Value}/../../workshop/content/{SteamManager.ApplicationId}";'
    new_ws = (
        '_steamWorkshopDirectory = global::System.OperatingSystem.IsAndroid()\n'
        '                ? $"{GameDirectory.Value}/Workshop"\n'
        '                : $"{GameDirectory.Value}/../../workshop/content/{SteamManager.ApplicationId}";'
    )
    if old_ws in ct and 'GameDirectory.Value}/Workshop' not in ct:
        ct = ct.replace(old_ws, new_ws)
        cm_changed = True
    old_gd = "_gameDirectory = Directory.GetCurrentDirectory();"
    new_gd = (
        "_gameDirectory = Directory.GetCurrentDirectory();\n"
        '            if (global::System.OperatingSystem.IsAndroid() && (string.IsNullOrEmpty(_gameDirectory) || _gameDirectory == "/") && !string.IsNullOrEmpty(WobbleGame.WorkingDirectory))\n'
        "                _gameDirectory = WobbleGame.WorkingDirectory.TrimEnd('/');"
    )
    if old_gd in ct and "WobbleGame.WorkingDirectory.TrimEnd" not in ct:
        ct = ct.replace(old_gd, new_gd, 1)
        cm_changed = True 
    if cm_changed:
        cm.write_text(ct, encoding="utf-8")

scm = root / "Quaver.Shared" / "Config" / "StructuredConfigManager.cs"
if scm.is_file():
    st = scm.read_text(encoding="utf-8-sig")
    if "internal static async Task WriteConfigFileAsync()" in st:
        st = st.replace(
            "internal static async Task WriteConfigFileAsync()",
            "internal static Task WriteConfigFileAsync()",
        )
        st = st.replace(
            "await using var sw = new StreamWriter(configFilePath);",
            "using var sw = new StreamWriter(configFilePath);",
        )
        st = st.replace(
            "        LastWrite = GameBase.Game?.TimeRunning ?? -1;\n    }",
            "        LastWrite = GameBase.Game?.TimeRunning ?? -1;\n        return Task.CompletedTask;\n    }",
        )
        scm.write_text(st, encoding="utf-8")
        # 3b) TextureManager: thread-safe Load y LoadAtlas (evita ArgumentException al cargar menu y select en paralelo)
tm_cs = root / "Wobble" / "Wobble" / "Managers" / "TextureManager.cs"
if tm_cs.is_file():
    tmt = tm_cs.read_text(encoding="utf-8-sig")
    if "LoadLock" not in tmt:
        tmt = tmt.replace(
            "        public static Dictionary<string, Texture2D> Textures { get; } = new Dictionary<string, Texture2D>();",
            "        private static readonly object LoadLock = new object();\n\n        public static Dictionary<string, Texture2D> Textures { get; } = new Dictionary<string, Texture2D>();",
            1,
        )
        old_load = (
            "        public static Texture2D Load(string name)\n"
            "        {\n"
            "            if (Textures.ContainsKey(name))\n"
            "                return Textures[name];\n\n"
            "            var tex = AssetLoader.LoadTexture2D(GameBase.Game.Resources.Get(name));\n"
            "            Textures.Add(name, tex);\n\n"
            "            return tex;\n"
            "        }"
        )
        new_load = (
            "        public static Texture2D Load(string name)\n"
            "        {\n"
            "            lock (LoadLock)\n"
            "            {\n"
            "                if (Textures.TryGetValue(name, out var existing))\n"
            "                    return existing;\n\n"
            "                var tex = AssetLoader.LoadTexture2D(GameBase.Game.Resources.Get(name));\n"
            "                Textures[name] = tex;\n"
            "                return tex;\n"
            "            }\n"
            "        }"
        )
        old_atlas = (
            "        public static List<Texture2D> LoadAtlas(string name, int rows, int columns)\n"
            "        {\n"
            "            if (TextureAtlases.ContainsKey(name))\n"
            "                return TextureAtlases[name];\n\n"
            "            var tex = AssetLoader.LoadTexture2D(GameBase.Game.Resources.Get(name));\n"
            "            var textures = AssetLoader.LoadSpritesheetFromTexture(tex, rows, columns);\n"
            "            tex.Dispose();\n\n"
            "            TextureAtlases.Add(name, textures);\n\n"
            "            return textures;\n"
            "        }"
        )
        new_atlas = (
            "        public static List<Texture2D> LoadAtlas(string name, int rows, int columns)\n"
            "        {\n"
            "            lock (LoadLock)\n"
            "            {\n"
            "                if (TextureAtlases.TryGetValue(name, out var existing))\n"
            "                    return existing;\n\n"
            "                var tex = AssetLoader.LoadTexture2D(GameBase.Game.Resources.Get(name));\n"
            "                var textures = AssetLoader.LoadSpritesheetFromTexture(tex, rows, columns);\n"
            "                tex.Dispose();\n\n"
            "                TextureAtlases[name] = textures;\n"
            "                return textures;\n"
            "            }\n"
            "        }"
        )
        tmt = tmt.replace(old_load, new_load, 1).replace(old_atlas, new_atlas, 1)
        tm_cs.write_text(tmt, encoding="utf-8") 

# 4) WobbleGame: MainThreadId en hilo GL, evitar ImGui/cimgui en Android Debug, y trazas Initialize/LoadContent
wg = root / "Wobble" / "Wobble" / "WobbleGame.cs"
if wg.is_file():
    wt = wg.read_text(encoding="utf-8-sig")
    changed = False
    if "public int MainThreadId { get; }" in wt:
        wt = wt.replace(
            "public int MainThreadId { get; }",
            "public int MainThreadId { get; private set; }",
        )
        changed = True
    old_init = (
        "        protected override void Initialize()\n"
        "        {\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.Initialize profile=" + GraphicsDevice?.GraphicsProfile);\n'
        '            Resources.AddStore(new DllResourceStore("Wobble.Resources.dll"));\n\n'
        "            LogManager.Initialize();\n"
        "            AudioManager.Initialize(DevicePeriod, DeviceBufferLength);\n"
        "            Window.ClientSizeChanged += WindowManager.OnClientSizeChanged;\n\n"
        "            base.Initialize();\n"
        "        }"
    )
    new_init = (
        "        protected override void Initialize()\n"
        "        {\n"
        "            MainThreadId = System.Threading.Thread.CurrentThread.ManagedThreadId;\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.Initialize start tid=" + MainThreadId + " profile=" + GraphicsDevice?.GraphicsProfile);\n'
        "            try\n"
        "            {\n"
        '                Resources.AddStore(new DllResourceStore("Wobble.Resources.dll"));\n\n'
        "                LogManager.Initialize();\n"
        "                AudioManager.Initialize(DevicePeriod, DeviceBufferLength);\n"
        "                Window.ClientSizeChanged += WindowManager.OnClientSizeChanged;\n\n"
        "                base.Initialize();\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.Initialize ok");\n'
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Fatal("WobbleGame.Initialize", ex);\n'
        "                throw;\n"
        "            }\n"
        "        }"
    )
    if old_init in wt:
        wt = wt.replace(old_init, new_init)
        changed = True
    old_wl = "            SpriteBatch = new SpriteBatch(GraphicsDevice);\n            WobbleAssets.Load();"
    new_wl = (
        "            MainThreadId = System.Threading.Thread.CurrentThread.ManagedThreadId;\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start tid=" + MainThreadId + " gd=" + (GraphicsDevice != null));\n'
        "            try\n"
        "            {\n"
        "                SpriteBatch = new SpriteBatch(GraphicsDevice);\n"
        "                WobbleAssets.Load();\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent ok");\n'
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Fatal("WobbleGame.LoadContent", ex);\n'
        "                throw;\n"
        "            }"
    )
    if old_wl in wt and "WobbleGame.LoadContent start" not in wt:
        wt = wt.replace(old_wl, new_wl)
        changed = True
    elif 'global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start gd=" + (GraphicsDevice != null));' in wt:
        wt = wt.replace(
            'global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start gd=" + (GraphicsDevice != null));',
            'MainThreadId = System.Threading.Thread.CurrentThread.ManagedThreadId;\n            global::Wobble.Logging.AndroidDiagnostics.Trace("WobbleGame.LoadContent start tid=" + MainThreadId + " gd=" + (GraphicsDevice != null));',
        )
        changed = True
    if "#if DEBUG\n            DebugOverlay = new DebugOverlay();\n#endif" in wt:
        wt = wt.replace(
            "#if DEBUG\n            DebugOverlay = new DebugOverlay();\n#endif",
            "#if DEBUG\n            if (!global::System.OperatingSystem.IsAndroid())\n                DebugOverlay = new DebugOverlay();\n#endif",
        )
        changed = True
    if changed:
        wg.write_text(wt, encoding="utf-8")

# 4b) Drawable.~Drawable: proteger Destroy() en el hilo Finalizer para evitar crashes AppDomain si falla un ctor parcial
drw = root / "Wobble" / "Wobble" / "Graphics" / "Drawable.cs"
if drw.is_file():
    dt = drw.read_text(encoding="utf-8-sig")
    old_fin = (
        "        ~Drawable()\n"
        "        {\n"
        "            if (IsDisposed)\n"
        "                return;\n\n"
        "            Destroy();\n"
        "            IsDisposed = true;\n"
        "        }"
    )
    new_fin = (
        "        ~Drawable()\n"
        "        {\n"
        "            if (IsDisposed)\n"
        "                return;\n\n"
        "            try\n"
        "            {\n"
        "                Destroy();\n"
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                try { global::Wobble.Logging.AndroidDiagnostics.Trace("Drawable.Finalize: " + ex.GetType().Name + ": " + ex.Message); } catch { }\n'
        "            }\n\n"
        "            IsDisposed = true;\n"
        "        }"
    )
    if old_fin in dt and "Drawable.Finalize:" not in dt:
        dt = dt.replace(old_fin, new_fin)
        drw.write_text(dt, encoding="utf-8")

# 5) QuaverGame: trazas y captura de errores en Initialize, LoadContent y FirstUpdate
qg = root / "Quaver.Shared" / "QuaverGame.cs"
if qg.is_file():
    qt = qg.read_text(encoding="utf-8-sig")
    q_changed = False
    old_qi = "        protected override void Initialize()\n        {\n            QuaverScreenManager.Initialize();"
    new_qi = (
        "        protected override void Initialize()\n"
        "        {\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.Initialize start");\n'
        "            try\n"
        "            {\n"
        "                QuaverScreenManager.Initialize();"
    )
    old_qi_end = "            base.Initialize();\n        }\n\n        /// <inheritdoc />\n        /// <summary>\n        ///     LoadContent"
    new_qi_end = (
        "                base.Initialize();\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.Initialize ok");\n'
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Fatal("QuaverGame.Initialize", ex);\n'
        "                throw;\n"
        "            }\n"
        "        }\n\n        /// <inheritdoc />\n        /// <summary>\n        ///     LoadContent"
    )
    if old_qi in qt and old_qi_end in qt and "QuaverGame.Initialize start" not in qt:
        qt = qt.replace(old_qi, new_qi).replace(old_qi_end, new_qi_end)
        q_changed = True

    old_ql = "            base.LoadContent();\n            GlobalIcons.Load();"
    new_ql = (
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.LoadContent begin");\n'
        "            try\n"
        "            {\n"
        "                base.LoadContent();\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.LoadContent icons/flags");\n'
        "                GlobalIcons.Load();"
    )
    old_ql_end = "            QuaverScreenManager.ScheduleScreenChange(() => QuaverScreenFactory.CreateInitialization(), true);\n#endif"
    new_ql_end = (
        "                QuaverScreenManager.ScheduleScreenChange(() => QuaverScreenFactory.CreateInitialization(), true);\n"
        "#endif\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.LoadContent done");\n'
        "            }\n"
        "            catch (Exception ex)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Fatal("QuaverGame.LoadContent", ex);\n'
        "                throw;\n"
        "            }"
    )
    if old_ql in qt and old_ql_end in qt and "QuaverGame.LoadContent begin" not in qt:
        qt = qt.replace(old_ql, new_ql).replace(old_ql_end, new_ql_end)
        q_changed = True

    old_fu = (
        "            if (!FirstUpdateCalled)\n"
        "            {\n"
        "                InitializeFpsLimiting();\n\n"
        "                // Create the online hub on the first update, since it uses text, and we have to wait for things to\n"
        "                // be initialized\n"
        "                OnlineHub = new OnlineHub();\n"
        "                OnlineChat = new OnlineChat();\n"
        "                TooltipManager.TargetEligibilityFilter = target => OnlineChat.AllowsTooltip(target);\n"
        "                VolumeController = new VolumeControl();\n"
        "                FirstUpdateCalled = true;\n"
        "            }"
    )
    new_fu = (
        "            if (!FirstUpdateCalled)\n"
        "            {\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.FirstUpdate start");\n'
        "                try\n"
        "                {\n"
        "                    InitializeFpsLimiting();\n"
        "                    OnlineHub = new OnlineHub();\n"
        "                    OnlineChat = new OnlineChat();\n"
        "                    TooltipManager.TargetEligibilityFilter = target => OnlineChat.AllowsTooltip(target);\n"
        "                    VolumeController = new VolumeControl();\n"
        "                    FirstUpdateCalled = true;\n"
        '                    global::Wobble.Logging.AndroidDiagnostics.Trace("QuaverGame.FirstUpdate ok");\n'
        "                }\n"
        "                catch (Exception ex)\n"
        "                {\n"
        '                    global::Wobble.Logging.AndroidDiagnostics.Fatal("QuaverGame.FirstUpdate", ex);\n'
        "                    throw;\n"
        "                }\n"
        "            }"
    )
    if old_fu in qt and "QuaverGame.FirstUpdate start" not in qt:
        qt = qt.replace(old_fu, new_fu)
        q_changed = True
    old_bl = "            ConfigManager.WindowBorderless.ValueChanged += (sender, e) => Window.IsBorderless = e.Value;"
    new_bl = (
        "            ConfigManager.WindowBorderless.ValueChanged += (sender, e) =>\n"
        "            {\n"
        "                if (!global::System.OperatingSystem.IsAndroid())\n"
        "                    Window.IsBorderless = e.Value;\n"
        "            };"
    )
    if old_bl in qt:
        qt = qt.replace(old_bl, new_bl, 1)
        q_changed = True

    old_bl0 = "            Window.IsBorderless = ConfigManager.WindowBorderless.Value;"
    new_bl0 = (
        "            if (!global::System.OperatingSystem.IsAndroid())\n"
        "                Window.IsBorderless = ConfigManager.WindowBorderless.Value;"
    )
    if old_bl0 in qt:
        qt = qt.replace(old_bl0, new_bl0, 1)
        q_changed = True 

    if q_changed:
        qg.write_text(qt, encoding="utf-8")

# 5b) SkinStore, OptionsMenu, OptionsDialog, OptionsItems y EditScreen: evitar DirectoryNotFoundException / NullReferenceException
sk = root / "Quaver.Shared" / "Skinning" / "SkinStore.cs"
if sk.is_file():
    skt = sk.read_text(encoding="utf-8-sig")
    old_gs = (
        "            var skinDirectories = Directory.GetDirectories(ConfigManager.SkinDirectory.Value);\n\n"
        "            var dirs = skinDirectories.Select(dir => new DirectoryInfo(dir).Name);\n"
        "            skins.AddRange(dirs.ToList());\n\n"
        "            var workshopDirectories = Directory.GetDirectories(ConfigManager.SteamWorkshopDirectory.Value);"
    )
    new_gs = (
        "            var skinDir = ConfigManager.SkinDirectory?.Value;\n"
        "            var skinDirectories = !string.IsNullOrEmpty(skinDir) && Directory.Exists(skinDir)\n"
        "                ? Directory.GetDirectories(skinDir)\n"
        "                : global::System.Array.Empty<string>();\n\n"
        "            var dirs = skinDirectories.Select(dir => new DirectoryInfo(dir).Name);\n"
        "            skins.AddRange(dirs.ToList());\n\n"
        "            var workshopDir = ConfigManager.SteamWorkshopDirectory?.Value;\n"
        "            var workshopDirectories = !string.IsNullOrEmpty(workshopDir) && Directory.Exists(workshopDir)\n"
        "                ? Directory.GetDirectories(workshopDir)\n"
        "                : global::System.Array.Empty<string>();"
    )
    if old_gs in skt:
        skt = skt.replace(old_gs, new_gs)
        sk.write_text(skt, encoding="utf-8")

om = root / "Quaver.Shared" / "Screens" / "Options" / "OptionsMenu.cs"
if om.is_file():
    omt = om.read_text(encoding="utf-8-sig")
    old_omd = (
        "        public override void Destroy()\n"
        "        {\n"
        "            // ReSharper disable once DelegateSubtraction\n"
        "            SelectedSection.ValueChanged -= OnSectionChanged;\n"
        "            SelectedSection?.Dispose();\n"
        "            CurrentSearchQuery?.Dispose();\n"
        "            IsOptionFocused?.Dispose();\n\n"
        "            // Make sure to destroy everything that's not visible\n"
        "            foreach (var section in Sections)\n"
        "            {\n"
        "                foreach (var subcategory in section.Subcategories)\n"
        "                {\n"
        "                    foreach (var item in subcategory.Items)\n"
        "                    {\n"
        "                        item?.Destroy();\n"
        "                    }\n"
        "                }\n"
        "            }\n\n"
        "            base.Destroy();\n"
        "        }"
    )
    new_omd = (
        "        public override void Destroy()\n"
        "        {\n"
        "            if (SelectedSection != null)\n"
        "            {\n"
        "                // ReSharper disable once DelegateSubtraction\n"
        "                SelectedSection.ValueChanged -= OnSectionChanged;\n"
        "                SelectedSection.Dispose();\n"
        "            }\n"
        "            CurrentSearchQuery?.Dispose();\n"
        "            IsOptionFocused?.Dispose();\n\n"
        "            // Make sure to destroy everything that's not visible\n"
        "            if (Sections != null)\n"
        "            {\n"
        "                foreach (var section in Sections)\n"
        "                {\n"
        "                    if (section?.Subcategories == null)\n"
        "                        continue;\n\n"
        "                    foreach (var subcategory in section.Subcategories)\n"
        "                    {\n"
        "                        if (subcategory?.Items == null)\n"
        "                            continue;\n\n"
        "                        foreach (var item in subcategory.Items)\n"
        "                        {\n"
        "                            item?.Destroy();\n"
        "                        }\n"
        "                    }\n"
        "                }\n"
        "            }\n\n"
        "            base.Destroy();\n"
        "        }"
    )
    if old_omd in omt:
        omt = omt.replace(old_omd, new_omd)
        om.write_text(omt, encoding="utf-8")

od = root / "Quaver.Shared" / "Screens" / "Options" / "OptionsDialog.cs"
if od.is_file():
    odt = od.read_text(encoding="utf-8-sig")
    if "GlobalInputToken.Dispose();" in odt:
        odt = odt.replace("GlobalInputToken.Dispose();", "GlobalInputToken?.Dispose();")
        od.write_text(odt, encoding="utf-8")

ocs = root / "Quaver.Shared" / "Screens" / "Options" / "Items" / "Custom" / "OptionsItemCustomSkin.cs"
if ocs.is_file():
    ocst = ocs.read_text(encoding="utf-8-sig")
    old_gsi = "            if (skin == null)\n                return 0;"
    new_gsi = "            if (skin == null || string.IsNullOrEmpty(skin.Value))\n                return 0;"
    if old_gsi in ocst:
        ocst = ocst.replace(old_gsi, new_gsi)
        ocs.write_text(ocst, encoding="utf-8")

osr = root / "Quaver.Shared" / "Screens" / "Options" / "Items" / "Custom" / "OptionsItemScreenResolution.cs"
if osr.is_file():
    osrt = osr.read_text(encoding="utf-8-sig")
    old_modes = (
        "            foreach (DisplayMode mode in GraphicsAdapter.DefaultAdapter.SupportedDisplayModes)\n"
        "            {\n"
        '                var option = $"{mode.Width}x{mode.Height}";\n\n'
        "                if (!options.Contains(option))\n"
        "                    options.Add(option);\n"
        "            }"
    )
    new_modes = (
        "            try\n"
        "            {\n"
        "                foreach (DisplayMode mode in GraphicsAdapter.DefaultAdapter.SupportedDisplayModes)\n"
        "                {\n"
        '                    var option = $"{mode.Width}x{mode.Height}";\n\n'
        "                    if (!options.Contains(option))\n"
        "                        options.Add(option);\n"
        "                }\n"
        "            }\n"
        "            catch\n"
        "            {\n"
        "            }"
    )
    if old_modes in osrt and "try\n            {\n                foreach (DisplayMode mode" not in osrt:
        osrt = osrt.replace(old_modes, new_modes)
        osr.write_text(osrt, encoding="utf-8")

oao = root / "Quaver.Shared" / "Screens" / "Options" / "Items" / "Custom" / "OptionsItemAudioOutputDevice.cs"
if oao.is_file():
    oaot = oao.read_text(encoding="utf-8-sig")
    old_ao = (
        "        private static List<string> GetOptions()\n"
        "        {\n"
        "            var options = new List<string>();\n\n"
        "            for (var i = 1; i < Bass.DeviceCount; i++)\n"
        "                options.Add(Bass.GetDeviceInfo(i).Name);\n\n"
        "            return options;\n"
        "        }"
    )
    new_ao = (
        "        private static List<string> GetOptions()\n"
        "        {\n"
        "            var options = new List<string>();\n\n"
        "            try\n"
        "            {\n"
        "                for (var i = 1; i < Bass.DeviceCount; i++)\n"
        "                {\n"
        "                    var name = Bass.GetDeviceInfo(i).Name;\n"
        "                    if (!string.IsNullOrWhiteSpace(name))\n"
        "                        options.Add(name);\n"
        "                }\n"
        "            }\n"
        "            catch\n"
        "            {\n"
        "            }\n\n"
        "            if (options.Count == 0)\n"
        '                options.Add("Default");\n\n'
        "            return options;\n"
        "        }"
    )
    if old_ao in oaot:
        oaot = oaot.replace(old_ao, new_ao)
        oao.write_text(oaot, encoding="utf-8")

es = root / "Quaver.Shared" / "Screens" / "Edit" / "EditScreen.cs"
if es.is_file():
    est = es.read_text(encoding="utf-8-sig")
    old_lp = (
        "        private void LoadPluginsFromDirectory(string dir, bool isWorkshop)\n"
        "        {\n"
        "            foreach (var directory in Directory.GetDirectories(dir))"
    )
    new_lp = (
        "        private void LoadPluginsFromDirectory(string dir, bool isWorkshop)\n"
        "        {\n"
        "            if (string.IsNullOrEmpty(dir) || !Directory.Exists(dir))\n"
        "                return;\n\n"
        "            foreach (var directory in Directory.GetDirectories(dir))"
    )
    if old_lp in est:
        est = est.replace(old_lp, new_lp)
        es.write_text(est, encoding="utf-8")

# 6) MainActivity: HUD visible desde el primer instante + Safe Area (notch) + Haptica (Vibrator) + VIBRATE
manifest_xml = root / "android-head" / "AndroidManifest.xml"
if manifest_xml.is_file():
    mxt = manifest_xml.read_text(encoding="utf-8-sig")
    if "android.permission.VIBRATE" not in mxt:
        mxt = mxt.replace(
            '<uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />',
            '<uses-permission android:name="android.permission.MODIFY_AUDIO_SETTINGS" />\n  <uses-permission android:name="android.permission.VIBRATE" />',
        )
        manifest_xml.write_text(mxt, encoding="utf-8")

ma = root / "android-head" / "MainActivity.cs"
if ma.is_file():
    ma.write_text(r"""using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Android.App;
using Android.Content;
using Android.Content.PM;
using System.Collections.Generic;
using Android.Hardware.Input; 
using Android.OS;
using Android.Views;
using Android.Widget;
using Microsoft.Xna.Framework;
using Wobble.Logging;
using Wobble.Platform;

namespace QuaverAndroid
{
    [Activity(Label = "Quaver", Icon = "@drawable/icon", MainLauncher = true, LaunchMode = LaunchMode.SingleInstance,
        ScreenOrientation = ScreenOrientation.SensorLandscape,
        ConfigurationChanges = ConfigChanges.Orientation | ConfigChanges.Keyboard | ConfigChanges.KeyboardHidden | ConfigChanges.ScreenSize)]
    public class MainActivity : AndroidGameActivity, global::Android.Hardware.Input.InputManager.IInputDeviceListener
    {
        private string _crashFile;
        private Quaver.Shared.QuaverGame _game;
        private View _gameView;
        private FrameLayout _rootFrame;
        private TextView _statusText;
        private Handler _handler;
        private volatile bool _reportShown;
        private Vibrator _vibrator;
        private global::Android.Hardware.Input.InputManager _androidInputManager;
        private readonly Dictionary<int, string> _connectedGamepads = new Dictionary<int, string>(); 

        protected override void OnCreate(Bundle bundle)
        {
            base.OnCreate(bundle);
            Window?.AddFlags(WindowManagerFlags.KeepScreenOn | WindowManagerFlags.Fullscreen);
            if (Build.VERSION.SdkInt >= BuildVersionCodes.P && Window != null)
            {
                var lp = Window.Attributes;
                if (lp != null)
                {
                    lp.LayoutInDisplayCutoutMode = LayoutInDisplayCutoutMode.ShortEdges;
                    Window.Attributes = lp;
                }
            }

            var dataDir = FilesDir.AbsolutePath;
            Wobble.WobbleGame.WorkingDirectory = dataDir + "/";
            _crashFile = Path.Combine(dataDir, "informe-fallo.txt");
            HookCrashHandlers();
            InitHaptics();

            foreach (var dir in new[] { "Songs", "Skins", "Screenshots", "Replays", "Backup", "Logs", "Workshop" })
            {
                try { Directory.CreateDirectory(Path.Combine(dataDir, dir)); } catch { }
            }

            if (File.Exists(_crashFile))
            {
                ShowReport(File.ReadAllText(_crashFile));
                return;
            }

            _rootFrame = new FrameLayout(this);
            _rootFrame.SetBackgroundColor(global::Android.Graphics.Color.Black);

            _statusText = new TextView(this) { Text = "Iniciando Quaver..." };
            _statusText.SetTextColor(global::Android.Graphics.Color.Yellow);
            _statusText.SetBackgroundColor(global::Android.Graphics.Color.Argb(160, 0, 0, 0));
            _statusText.SetPadding(16, 8, 16, 8);
            _statusText.TextSize = 12;
            _rootFrame.AddView(_statusText, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent,
                GravityFlags.Top | GravityFlags.Left));

            var logsBtn = new Button(this) { Text = "LOGS", Focusable = false, FocusableInTouchMode = false }; 
            logsBtn.SetBackgroundColor(global::Android.Graphics.Color.Argb(210, 180, 30, 30));
            logsBtn.SetTextColor(global::Android.Graphics.Color.White);
            logsBtn.Click += (s, e) => ShowReport(BuildLogText());
            _rootFrame.AddView(logsBtn, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent,
                GravityFlags.Top | GravityFlags.Right));

            SetContentView(_rootFrame);
            UpdateSafeAreaInsets();
            _handler = new Handler(Looper.MainLooper);
            InitAndroidGamepadListener(); 
            ScheduleTracePoll();
            AndroidDiagnostics.Trace("01.OnCreate dataDir=" + dataDir);

            foreach (var lib in new[] { "bass", "bass_fx", "e_sqlite3", "SkiaSharp", "freetype", "openal32" })
            {
                try
                {
                    global::Java.Lang.JavaSystem.LoadLibrary(lib);
                    AndroidDiagnostics.Trace("LoadLibrary OK: " + lib);
                }
                catch (Exception ex)
                {
                    AndroidDiagnostics.Trace("LoadLibrary WARN " + lib + ": " + ex.Message);
                }
            }

            foreach (var asm in new[] { "Quaver.Resources", "Wobble.Resources" })
            {
                try
                {
                    System.Reflection.Assembly.Load(asm);
                    AndroidDiagnostics.Trace("Assembly.Load OK: " + asm);
                }
                catch (Exception ex)
                {
                    AndroidDiagnostics.Trace("Assembly.Load WARN " + asm + ": " + ex.Message);
                }
            }

            try
            {
                StartQuaver(dataDir + "/");
            }
            catch (Exception e)
            {
                WriteReport(e, "arranque");
                ShowReport(File.Exists(_crashFile) ? File.ReadAllText(_crashFile) : e.ToString());
            }
        }

        public override void OnAttachedToWindow()
        {
            base.OnAttachedToWindow();
            UpdateSafeAreaInsets();
        }

        public override void OnWindowFocusChanged(bool hasFocus)
        {
            base.OnWindowFocusChanged(hasFocus);
            if (hasFocus)
                UpdateSafeAreaInsets();
        }

        private void InitHaptics()
        {
            try
            {
                if (Build.VERSION.SdkInt >= BuildVersionCodes.S)
                {
                    var vm = GetSystemService(VibratorManagerService) as VibratorManager;
                    _vibrator = vm?.DefaultVibrator;
                }
                else
                {
#pragma warning disable CS0618
                    _vibrator = GetSystemService(VibratorService) as Vibrator;
#pragma warning restore CS0618
                }

                if (_vibrator != null && _vibrator.HasVibrator)
                {
                    AndroidPlatformBridge.HasVibrator = true;
                    AndroidPlatformBridge.VibrateHandler = (durationMs, amplitude) =>
                    {
                        try
                        {
                            if (_vibrator == null || !_vibrator.HasVibrator)
                                return;

                            if (Build.VERSION.SdkInt >= BuildVersionCodes.O)
                            {
                                var eff = VibrationEffect.CreateOneShot(durationMs, amplitude);
                                if (eff != null)
                                    _vibrator.Vibrate(eff);
                            }
                            else
                            {
#pragma warning disable CS0618
                                _vibrator.Vibrate(durationMs);
#pragma warning restore CS0618
                            }
                        }
                        catch
                        {
                        }
                    };
                }
            }
            catch
            {
            }
        }

        private void UpdateSafeAreaInsets()
        {
            try
            {
                var dm = Resources?.DisplayMetrics;
                var w = dm != null && dm.WidthPixels > 0 ? (float)dm.WidthPixels : 1f;
                var h = dm != null && dm.HeightPixels > 0 ? (float)dm.HeightPixels : 1f;
                var insets = Window?.DecorView?.RootWindowInsets;
                if (insets == null)
                    return;

                float left = 0f, top = 0f, right = 0f, bottom = 0f;
                if (Build.VERSION.SdkInt >= BuildVersionCodes.P)
                {
                    var cutout = insets.DisplayCutout;
                    if (cutout != null)
                    {
                        left = Math.Max(left, cutout.SafeInsetLeft / w);
                        top = Math.Max(top, cutout.SafeInsetTop / h);
                        right = Math.Max(right, cutout.SafeInsetRight / w);
                        bottom = Math.Max(bottom, cutout.SafeInsetBottom / h);
                    }
                }

                if (Build.VERSION.SdkInt >= BuildVersionCodes.R)
                {
                    var sys = insets.GetInsets(WindowInsets.Type.DisplayCutout() | WindowInsets.Type.SystemGestures());
                    if (sys != null)
                    {
                        left = Math.Max(left, sys.Left / w);
                        top = Math.Max(top, sys.Top / h);
                        right = Math.Max(right, sys.Right / w);
                        bottom = Math.Max(bottom, sys.Bottom / h);
                    }
                }

                AndroidPlatformBridge.SafeInsetLeft = Math.Min(0.25f, Math.Max(0f, left));
                AndroidPlatformBridge.SafeInsetTop = Math.Min(0.25f, Math.Max(0f, top));
                AndroidPlatformBridge.SafeInsetRight = Math.Min(0.25f, Math.Max(0f, right));
                AndroidPlatformBridge.SafeInsetBottom = Math.Min(0.25f, Math.Max(0f, bottom));
            }
            catch
            {
            }
        }

        private void StartQuaver(string workDir)
        {
           Wobble.WobbleGame.WorkingDirectory = workDir;
            System.IO.Directory.SetCurrentDirectory(workDir);
            System.Environment.CurrentDirectory = workDir;
            AndroidDiagnostics.Trace("02.Batteries_V2.Init");
            SQLitePCL.Batteries_V2.Init();
            AndroidDiagnostics.Trace("03.ConfigManager.Initialize");
            Wobble.Logging.Logger.Initialize();
            Quaver.Shared.Config.ConfigManager.Initialize();
            Quaver.Shared.Config.StructuredConfigManager.Initialize();  
            System.Globalization.CultureInfo.DefaultThreadCurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
            System.Globalization.CultureInfo.DefaultThreadCurrentUICulture = System.Globalization.CultureInfo.InvariantCulture;
            System.Threading.Thread.CurrentThread.CurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
            System.Threading.Thread.CurrentThread.CurrentUICulture = System.Globalization.CultureInfo.InvariantCulture;
            AndroidDiagnostics.Trace("04.new QuaverGame");
            _game = new Quaver.Shared.QuaverGame();
            _gameView = (View)_game.Services.GetService(typeof(View));
            AndroidDiagnostics.Trace("05.AttachGameView view=" + (_gameView != null));
            if (_gameView != null && _rootFrame != null)
            {
                _rootFrame.AddView(_gameView, 0, new FrameLayout.LayoutParams(
                    ViewGroup.LayoutParams.MatchParent, ViewGroup.LayoutParams.MatchParent));
            }
            UpdateSafeAreaInsets();
            AndroidDiagnostics.Trace("06.game.Run()");
            _game.Run();
        }

        private void ScheduleTracePoll()
        {
            if (_reportShown)
                return;
            _handler?.PostDelayed(() =>
            {
                if (_reportShown)
                    return;
                try
                {
                    var tracePath = Path.Combine(FilesDir.AbsolutePath, "Logs", "boot-trace.log");
                    if (File.Exists(tracePath) && _statusText != null)
                    {
                        var lines = ReadTailShared(tracePath, 1024).TrimEnd().Split('\n');
                        if (lines.Length > 0)
                            _statusText.Text = lines[lines.Length - 1].Trim();
                    }
                }
                catch { }
                ScheduleTracePoll();
            }, 600);
        }

        private void HookCrashHandlers()
        {
            AppDomain.CurrentDomain.UnhandledException += (s, e) =>
            {
                var ex = e.ExceptionObject as Exception;
                WriteReport(ex, "AppDomain");
                TryShowFatalUi(ex != null ? ex.ToString() : "(sin excepcion)");
            };
            Android.Runtime.AndroidEnvironment.UnhandledExceptionRaiser += (s, e) =>
            {
                WriteReport(e.Exception, "Android");
                TryShowFatalUi(e.Exception != null ? e.Exception.ToString() : "(sin excepcion)");
            };
            TaskScheduler.UnobservedTaskException += (s, e) =>
            {
                WriteReport(e.Exception, "UnobservedTask");
                e.SetObserved();
            };
            AndroidDiagnostics.OnFatal += msg =>
            {
                WriteTextReport("TaskHandler/Fatal", msg);
                TryShowFatalUi(msg);
            };
        }

        private void TryShowFatalUi(string msg)
        {
            if (_reportShown)
                return;
            try
            {
                RunOnUiThread(() =>
                {
                    if (_reportShown)
                        return;
                    ShowReport(BuildLogText() + "\n\n=== EXCEPCION ===\n" + msg);
                });
            }
            catch { }
        }

        private void WriteTextReport(string origin, string body)
        {
            try
            {
                var sb = new StringBuilder();
                sb.AppendLine("Quaver Android (comunitario) - informe de fallo");
                sb.AppendLine("Origen: " + origin);
                sb.AppendLine("Hora UTC: " + DateTime.UtcNow.ToString("u"));
                sb.AppendLine("Dispositivo: " + Build.Manufacturer + " " + Build.Model + " / Android " + Build.VERSION.Release + " (API " + (int)Build.VERSION.SdkInt + ")");
                sb.AppendLine();
                sb.AppendLine(body);
                if (File.Exists(_crashFile) && new FileInfo(_crashFile).Length < 65536)
                    File.AppendAllText(_crashFile, "\n\n--- REGISTRO ADICIONAL ---\n\n" + sb);
                else
                    File.WriteAllText(_crashFile, sb.ToString());
                Android.Util.Log.Error("QuaverAndroid", sb.ToString());
            }
            catch { }
        }

        private void WriteReport(Exception ex, string origin) =>
            WriteTextReport(origin, ex != null ? ex.ToString() : "(sin excepcion)");

        private static string ReadShared(string path)
        {
            using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            using (var sr = new StreamReader(fs))
                return sr.ReadToEnd();
        }

        private static string ReadTailShared(string path, int maxBytes)
        {
            using (var fs = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.ReadWrite))
            {
                if (fs.Length > maxBytes)
                    fs.Seek(-maxBytes, SeekOrigin.End);
                using (var sr = new StreamReader(fs))
                    return sr.ReadToEnd();
            }
        }

        private void InitAndroidGamepadListener()
        {
            try
            {
                _androidInputManager = GetSystemService(InputService) as global::Android.Hardware.Input.InputManager;
                if (_androidInputManager == null)
                    return;

                _androidInputManager.RegisterInputDeviceListener(this, _handler);
                var ids = _androidInputManager.GetInputDeviceIds();
                if (ids != null)
                {
                    foreach (var id in ids)
                    {
                        var dev = InputDevice.GetDevice(id);
                        if (IsGamepadDevice(dev))
                        {
                            var name = string.IsNullOrWhiteSpace(dev.Name) ? $"Mando #{id}" : dev.Name;
                            _connectedGamepads[id] = name;
                            AndroidPlatformBridge.NotifyGamepadConnection(name, true);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                AndroidDiagnostics.Trace("InitAndroidGamepadListener ERR: " + ex.Message);
            }
        }

        private static bool IsGamepadDevice(InputDevice dev)
        {
            if (dev == null || dev.IsVirtual)
                return false;
            var src = (int)dev.Sources;
            return (src & 0x00000400) != 0 || (src & 0x01000000) != 0;
        }

        public void OnInputDeviceAdded(int deviceId)
        {
            try
            {
                var dev = InputDevice.GetDevice(deviceId);
                if (!IsGamepadDevice(dev))
                    return;
                var name = string.IsNullOrWhiteSpace(dev.Name) ? $"Mando #{deviceId}" : dev.Name;
                _connectedGamepads[deviceId] = name;
                AndroidPlatformBridge.NotifyGamepadConnection(name, true);
            }
            catch { }
        }

        public void OnInputDeviceChanged(int deviceId)
        {
            try
            {
                var dev = InputDevice.GetDevice(deviceId);
                if (IsGamepadDevice(dev) && !_connectedGamepads.ContainsKey(deviceId))
                {
                    var name = string.IsNullOrWhiteSpace(dev.Name) ? $"Mando #{deviceId}" : dev.Name;
                    _connectedGamepads[deviceId] = name;
                    AndroidPlatformBridge.NotifyGamepadConnection(name, true);
                }
            }
            catch { }
        }

        public void OnInputDeviceRemoved(int deviceId)
        {
            try
            {
                if (_connectedGamepads.TryGetValue(deviceId, out var name))
                {
                    _connectedGamepads.Remove(deviceId);
                    AndroidPlatformBridge.NotifyGamepadConnection(name, false);
                }
            }
            catch { }
        }

        protected override void OnDestroy()
        {
            try
            {
                _androidInputManager?.UnregisterInputDeviceListener(this);
            }
            catch { }
            base.OnDestroy();
        }

        public override bool DispatchKeyEvent(KeyEvent e)
        {
            if (e != null && e.KeyCode == Keycode.VolumeDown && e.Action == KeyEventActions.Down)
            {
                try
                {
                    ShowReport(BuildLogText());
                }
                catch (Exception ex)
                {
                    Android.Util.Log.Error("QuaverAndroid", ex.ToString());
                }
                return true;
            }

            if (e != null && !_reportShown)
            {
                var kc = (int)e.KeyCode;
                var src = (int)e.Source;
                var isGamepadSource = (src & 0x00000400) != 0 || (src & 0x01000000) != 0;
                if (kc == 4 && !isGamepadSource) // Keycode.Back sistema
                {
                    if (e.Action == KeyEventActions.Down && e.RepeatCount == 0)
                        AndroidPlatformBridge.IsNativeBackPressed = true;
                    else if (e.Action == KeyEventActions.Up)
                        AndroidPlatformBridge.IsNativeBackPressed = false;
                    return true;
                }

                var mappedKc = (kc == 4 && isGamepadSource) ? 97 : kc;
                var fromPad = isGamepadSource || (src & 0x00000200) != 0
                    || (kc >= 96 && kc <= 110) || (kc >= 19 && kc <= 23);
                if (fromPad && kc != 24 && kc != 25 && kc != 26)
                {
                    if (e.Device != null && !_connectedGamepads.ContainsKey(e.DeviceId) && IsGamepadDevice(e.Device))
                    {
                        var name = string.IsNullOrWhiteSpace(e.Device.Name) ? $"Mando #{e.DeviceId}" : e.Device.Name;
                        _connectedGamepads[e.DeviceId] = name;
                        AndroidPlatformBridge.NotifyGamepadConnection(name, true);
                    }

                    if (e.Action == KeyEventActions.Down)
                    {
                        if (e.RepeatCount == 0)
                            AndroidPlatformBridge.NotifyNativeGamepadButton(mappedKc, true);
                        return true;
                    }
                    if (e.Action == KeyEventActions.Up)
                    {
                        AndroidPlatformBridge.NotifyNativeGamepadButton(mappedKc, false);
                        return true;
                    }
                }
            }

            return base.DispatchKeyEvent(e);
        }

        public override bool DispatchGenericMotionEvent(MotionEvent e)
        {
            if (e != null && (((int)e.Source & 0x01000000) != 0 || ((int)e.Source & 0x00000400) != 0))
            {
                try
                {
                    if (e.Device != null && !_connectedGamepads.ContainsKey(e.DeviceId) && IsGamepadDevice(e.Device))
                    {
                        var name = string.IsNullOrWhiteSpace(e.Device.Name) ? $"Mando #{e.DeviceId}" : e.Device.Name;
                        _connectedGamepads[e.DeviceId] = name;
                        AndroidPlatformBridge.NotifyGamepadConnection(name, true);
                    }

                    var lx = e.GetAxisValue((Axis)0);
                    var ly = e.GetAxisValue((Axis)1);
                    var hx = e.GetAxisValue((Axis)15);
                    var hy = e.GetAxisValue((Axis)16);
                    var lt = Math.Max(e.GetAxisValue((Axis)17), e.GetAxisValue((Axis)23));
                    var rt = Math.Max(e.GetAxisValue((Axis)18), e.GetAxisValue((Axis)22));
                    AndroidPlatformBridge.NotifyNativeGamepadAxes(lx, ly, hx, hy, lt, rt);
                    return true;
                }
                catch { }
            }
            return base.DispatchGenericMotionEvent(e);
        }

        private string BuildLogText()
        {
            var sb = new StringBuilder();
            sb.AppendLine("Registro de Quaver Android (boot-trace + Logs)");
            var dir = Path.Combine(FilesDir.AbsolutePath, "Logs");
            if (!Directory.Exists(dir))
            {
                sb.AppendLine("(no existe la carpeta de registros: " + dir + ")");
                return sb.ToString();
            }
            foreach (var file in Directory.GetFiles(dir, "*.log"))
            {
                string[] lines;
                try
                {
                    lines = ReadShared(file).Split(new[] { Convert.ToChar(10) });
                }
                catch (Exception e)
                {
                    sb.AppendLine("No se pudo leer " + file + ": " + e.Message);
                    continue;
                }
                sb.AppendLine();
                sb.AppendLine("=== " + Path.GetFileName(file) + " (" + lines.Length + " lineas) ===");
                for (var i = Math.Max(0, lines.Length - 120); i < lines.Length; i++)
                    sb.AppendLine(lines[i].TrimEnd(Convert.ToChar(13)));
            }
            return sb.ToString();
        }

        private void ShowReport(string text)
        {
            _reportShown = true;
            if (_gameView != null)
                _gameView.Visibility = ViewStates.Gone;
            var layout = new LinearLayout(this) { Orientation = Orientation.Vertical };
            layout.SetBackgroundColor(global::Android.Graphics.Color.Rgb(20, 20, 28));
            layout.SetPadding(32, 32, 32, 32);

            var title = new TextView(this) { Text = "Quaver Android: informe" };
            title.TextSize = 18;
            title.SetTextColor(global::Android.Graphics.Color.White);

            var copy = new Button(this) { Text = "Copiar informe" };
            copy.Click += (s, e) =>
            {
                var cm = (ClipboardManager)GetSystemService(ClipboardService);
                cm.PrimaryClip = ClipData.NewPlainText("informe", text);
                Toast.MakeText(this, "Informe copiado", ToastLength.Short).Show();
            };

            var close = new Button(this) { Text = "Borrar informe y cerrar" };
            close.Click += (s, e) =>
            {
                try { File.Delete(_crashFile); } catch { }
                Android.OS.Process.KillProcess(Android.OS.Process.MyPid());
            };

            var body = new TextView(this) { Text = text };
            body.TextSize = 11;
            body.SetTextColor(global::Android.Graphics.Color.White);
            body.SetTextIsSelectable(true);

            layout.AddView(title);
            layout.AddView(copy);
            layout.AddView(close);
            layout.AddView(body);

            var scroll = new ScrollView(this);
            scroll.SetBackgroundColor(global::Android.Graphics.Color.Rgb(20, 20, 28));
            scroll.AddView(layout);
            SetContentView(scroll);
        }
    }
}
""", encoding="utf-8") 
    # 7) SteamManager y llamadas Steamworks seguras en Android (evitar DllNotFoundException: steam_api)
sm = root / "Quaver.Shared" / "Online" / "SteamManager.cs"
if sm.is_file():
    smt = sm.read_text(encoding="utf-8-sig")
    sm_changed = False

    old_appid = "        public static uint ApplicationId => 980610;"
    new_appid = (
        "        public static uint ApplicationId => 980610;\n\n"
        "        /// <summary>\n"
        "        ///     Devuelve el SteamID local si Steam está inicializado; 0 en Android/offline.\n"
        "        /// </summary>\n"
        "        public static ulong GetSteamIdOrZero() => IsInitialized ? SteamUser.GetSteamID().m_SteamID : 0;\n\n"
        "        /// <summary>\n"
        "        ///     Devuelve el nombre de Steam si está inicializado; ConfigManager.Username en Android/offline.\n"
        "        /// </summary>\n"
        '        public static string GetPersonaNameOrDefault() => IsInitialized ? SteamFriends.GetPersonaName() : (ConfigManager.Username?.Value ?? "Player");'
    )
    if old_appid in smt and "GetSteamIdOrZero()" not in smt:
        smt = smt.replace(old_appid, new_appid)
        sm_changed = True

    old_avatar_req = (
        "        public static void SendAvatarRetrievalRequest(ulong steamId) => ThreadScheduler.Run(() =>\n"
        "        {\n"
        "            var info = SteamFriends.RequestUserInformation(new CSteamID(steamId), false);\n"
        '            Logger.Debug($"Requested Steam user information for user: {steamId} - {info}", LogType.Network);\n\n'
        "            if (!info)\n"
        "                LoadAvatarIfNotExists(steamId);\n"
        "        });"
    )
    new_avatar_req = (
        "        public static void SendAvatarRetrievalRequest(ulong steamId)\n"
        "        {\n"
        "            if (global::System.OperatingSystem.IsAndroid() || !IsInitialized || steamId == 0)\n"
        "                return;\n\n"
        "            ThreadScheduler.Run(() =>\n"
        "            {\n"
        "                var info = SteamFriends.RequestUserInformation(new CSteamID(steamId), false);\n"
        '                Logger.Debug($"Requested Steam user information for user: {steamId} - {info}", LogType.Network);\n\n'
        "                if (!info)\n"
        "                    LoadAvatarIfNotExists(steamId);\n"
        "            });\n"
        "        }"
    )
    if old_avatar_req in smt:
        smt = smt.replace(old_avatar_req, new_avatar_req)
        sm_changed = True

    old_get_avatar = "            if (UserAvatars.ContainsKey(steamId))"
    new_get_avatar = "            if (UserAvatars != null && UserAvatars.ContainsKey(steamId))"
    if old_get_avatar in smt and new_get_avatar not in smt:
        smt = smt.replace(old_get_avatar, new_get_avatar)
        sm_changed = True

    if sm_changed:
        sm.write_text(smt, encoding="utf-8")

steam_id_callers = (
    "Quaver.Shared/Screens/Gameplay/Rulesets/Keys/GameplayRulesetKeys.cs",
    "Quaver.Shared/Screens/Gameplay/GameplayScreenView.cs",
    "Quaver.Shared/Screens/Gameplay/UI/Scoreboard/ScoreboardUser.cs",
    "Quaver.Shared/Screens/Results/UI/Header/Contents/ResultsScreenHeaderAvatar.cs",
    "Quaver.Shared/Screens/Selection/UI/Profile/LocalProfileBanner.cs",
    "Quaver.Shared/Screens/Selection/UI/Leaderboard/Components/DrawableLeaderboardScoreContainer.cs",
    "Quaver.Shared/Graphics/Menu/Border/Components/Users/DrawableLoggedInUser.cs",
    "Quaver.Shared/Graphics/Online/OnlinePlayercard.cs",
    "Quaver.Shared/Graphics/Online/Playercard/UserPlayercard.cs",
    "Quaver.Shared/Screens/V2/UI/ScreenNavigation.cs",
    "Quaver.Shared/Screens/Initialization/InitializationScreen.cs",
    "Quaver.Shared/Screens/V2/Initialization/InitializationScreen.cs",
    "Quaver.Shared/Graphics/Dialogs/Online/CreatingAccountDialog.cs",
    "Quaver.Shared/Graphics/Online/Username/UsernameSelectionTextbox.cs",
)
for rel in steam_id_callers:
    p = root / rel
    if not p.is_file():
        continue
    t = p.read_text(encoding="utf-8-sig")
    nt = t.replace(
        "SteamUser.GetSteamID().m_SteamID",
        "global::Quaver.Shared.Online.SteamManager.GetSteamIdOrZero()",
    ).replace(
        "SteamFriends.GetPersonaName()",
        "global::Quaver.Shared.Online.SteamManager.GetPersonaNameOrDefault()",
    )
    if nt != t:
        p.write_text(nt, encoding="utf-8")

sa = root / "Quaver.Shared" / "Online" / "SteamAchievements.cs"
if sa.is_file():
    sat = sa.read_text(encoding="utf-8-sig")
    sa_changed = False
    old_sa_ctor = "            UserStatsReceivedCallResult = CallResult<UserStatsReceived_t>.Create(OnUserStatsReceived);"
    new_sa_ctor = (
        "            if (SteamManager.IsInitialized)\n"
        "                UserStatsReceivedCallResult = CallResult<UserStatsReceived_t>.Create(OnUserStatsReceived);"
    )
    if old_sa_ctor in sat and "if (SteamManager.IsInitialized)\n                UserStatsReceivedCallResult" not in sat:
        sat = sat.replace(old_sa_ctor, new_sa_ctor)
        sa_changed = True

    old_sa_unlock = (
        "        public void Unlock()\n"
        "        {\n"
        "            var call = SteamUserStats.RequestUserStats(SteamUser.GetSteamID());"
    )
    new_sa_unlock = (
        "        public void Unlock()\n"
        "        {\n"
        "            if (!SteamManager.IsInitialized)\n"
        "            {\n"
        "                Complete();\n"
        "                return;\n"
        "            }\n\n"
        "            var call = SteamUserStats.RequestUserStats(SteamUser.GetSteamID());"
    )
    if old_sa_unlock in sat:
        sat = sat.replace(old_sa_unlock, new_sa_unlock)
        sa_changed = True
    if sa_changed:
        sa.write_text(sat, encoding="utf-8")

sw = root / "Quaver.Shared" / "Online" / "SteamWorkshopItem.cs"
if sw.is_file():
    swt = sw.read_text(encoding="utf-8-sig")
    sw_changed = False
    old_sw_up = (
        "        public void Upload()\n"
        "        {\n"
        "            Current = this;"
    )
    new_sw_up = (
        "        public void Upload()\n"
        "        {\n"
        "            if (!SteamManager.IsInitialized)\n"
        "            {\n"
        "                HasUploaded = true;\n"
        "                return;\n"
        "            }\n\n"
        "            Current = this;"
    )
    if old_sw_up in swt and "if (!SteamManager.IsInitialized)\n            {\n                HasUploaded = true;" not in swt:
        swt = swt.replace(old_sw_up, new_sw_up)
        sw_changed = True

    old_sw_prog = (
        "        public int GetUploadProgressPercentage()\n"
        "        {\n"
        "            SteamUGC.GetItemUpdateProgress(Handle, out var bytesProcessed, out var bytesTotal);"
    )
    new_sw_prog = (
        "        public int GetUploadProgressPercentage()\n"
        "        {\n"
        "            if (!SteamManager.IsInitialized)\n"
        "                return 0;\n\n"
        "            SteamUGC.GetItemUpdateProgress(Handle, out var bytesProcessed, out var bytesTotal);"
    )
    if old_sw_prog in swt:
        swt = swt.replace(old_sw_prog, new_sw_prog)
        sw_changed = True
    if sw_changed:
        sw.write_text(swt, encoding="utf-8")

# 8) Evitar ANR de arranque (>5s en hilo UI):
#    a) SkinManager.LoadEditorSkin(): tratar DefaultEditorSkin == null como igual a DefaultSkin (evita cargar el skin 2 veces)
skm = root / "Quaver.Shared" / "Skinning" / "SkinManager.cs"
if skm.is_file():
    skmt = skm.read_text(encoding="utf-8-sig")
    old_same = "var isSameDefaultSkin = ConfigManager.DefaultSkin.Value == ConfigManager.DefaultEditorSkin.Value;"
    new_same = "var isSameDefaultSkin = ConfigManager.DefaultEditorSkin.Value == null || ConfigManager.DefaultSkin.Value == ConfigManager.DefaultEditorSkin.Value;"
    if old_same in skmt:
        skmt = skmt.replace(old_same, new_same)
        skm.write_text(skmt, encoding="utf-8")

#    b) InitializationScreen: dividir fuentes (frame 1) / skin (frame 2) / InitializationTask (frame 3) para ceder al Looper Android
init_scr = root / "Quaver.Shared" / "Screens" / "Initialization" / "InitializationScreen.cs"
if init_scr.is_file():
    it = init_scr.read_text(encoding="utf-8-sig")
    old_ofu_traced = (
        "        public override void OnFirstUpdate()\n"
        "        {\n"
        "            GameBase.Game.GlobalUserInterface.Cursor.Alpha = 0;\n\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("InitScreen: Loading skin");\n'
        '            Logger.Important($"Loading skin...", LogType.Runtime);\n'
        "            // Avoid loading SoundEffects before Audio Device hasn't been set yet which leads to sound effects not working. \n"
        "            SkinManager.Load(UniversalSkinElementsLoadFlags.All & ~UniversalSkinElementsLoadFlags.SoundEffects);\n\n"
        '            Logger.Important($"Loading fonts...", LogType.Runtime);\n'
        "            Fonts.LoadWobbleFonts();\n\n"
        "            InitializationTask.Run(0);\n\n"
        "            base.OnFirstUpdate();\n"
        "        }"
    )
    old_ofu_plain = (
        "        public override void OnFirstUpdate()\n"
        "        {\n"
        "            GameBase.Game.GlobalUserInterface.Cursor.Alpha = 0;\n\n"
        '            Logger.Important($"Loading skin...", LogType.Runtime);\n'
        "            // Avoid loading SoundEffects before Audio Device hasn't been set yet which leads to sound effects not working. \n"
        "            SkinManager.Load(UniversalSkinElementsLoadFlags.All & ~UniversalSkinElementsLoadFlags.SoundEffects);\n\n"
        '            Logger.Important($"Loading fonts...", LogType.Runtime);\n'
        "            Fonts.LoadWobbleFonts();\n\n"
        "            InitializationTask.Run(0);\n\n"
        "            base.OnFirstUpdate();\n"
        "        }"
    )
    new_ofu = (
        "        private int _androidInitStep;\n\n"
        "        public override void OnFirstUpdate()\n"
        "        {\n"
        "            GameBase.Game.GlobalUserInterface.Cursor.Alpha = 0;\n\n"
        '            global::Wobble.Logging.AndroidDiagnostics.Trace("InitScreen: Loading fonts");\n'
        '            Logger.Important($"Loading fonts...", LogType.Runtime);\n'
        "            Fonts.LoadWobbleFonts();\n"
        "            _androidInitStep = 1;\n\n"
        "            base.OnFirstUpdate();\n"
        "        }\n\n"
        "        public override void Update(global::Microsoft.Xna.Framework.GameTime gameTime)\n"
        "        {\n"
        "            if (_androidInitStep == 1)\n"
        "            {\n"
        "                _androidInitStep = 2;\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("InitScreen: Loading skin");\n'
        '                Logger.Important($"Loading skin...", LogType.Runtime);\n'
        "                SkinManager.Load(UniversalSkinElementsLoadFlags.All & ~UniversalSkinElementsLoadFlags.SoundEffects);\n"
        "                base.Update(gameTime);\n"
        "                return;\n"
        "            }\n\n"
        "            if (_androidInitStep == 2)\n"
        "            {\n"
        "                _androidInitStep = 3;\n"
        '                global::Wobble.Logging.AndroidDiagnostics.Trace("InitScreen: InitializationTask.Run");\n'
        "                InitializationTask.Run(0);\n"
        "            }\n\n"
        "            base.Update(gameTime);\n"
        "        }"
    )
    if old_ofu_traced in it:
        it = it.replace(old_ofu_traced, new_ofu)
        init_scr.write_text(it, encoding="utf-8")
    elif old_ofu_plain in it:
        it = it.replace(old_ofu_plain, new_ofu)
        init_scr.write_text(it, encoding="utf-8") 
        # 11) Wobble.Graphics.Shaders.Shader: validacion defensiva de byte[]/MGFX antes de BinaryReader, try-catch y fallback MissingShader
shader_cs = root / "Wobble" / "Wobble" / "Graphics" / "Shaders" / "Shader.cs"
if shader_cs.is_file():
    st = shader_cs.read_text(encoding="utf-8-sig")
    if "MissingShader" not in st:
        has_diag = (root / "Wobble" / "Wobble" / "Logging" / "AndroidDiagnostics.cs").is_file()
        diag_trace = '            global::Wobble.Logging.AndroidDiagnostics.Trace(msg);\n' if has_diag else ''
        new_shader = (
            "using System;\n"
            "using System.Collections.Generic;\n"
            "using System.Diagnostics;\n"
            "using System.IO;\n"
            "using Microsoft.Xna.Framework;\n"
            "using Microsoft.Xna.Framework.Graphics;\n"
            "using Wobble.Logging;\n\n"
            "namespace Wobble.Graphics.Shaders\n"
            "{\n"
            "    public class Shader : IDisposable\n"
            "    {\n"
            '        private const int MgfxHeaderSignature = 0x5846474D; // "MGFX"\n'
            "        private const int MinMgfxHeaderLength = 10;\n"
            '        public const string MissingShaderName = "MissingShader";\n\n'
            "        /// <summary>\n"
            "        ///     The loaded shader effect.\n"
            "        /// </summary>\n"
            "        public Effect ShaderEffect { get; set; }\n\n"
            "        /// <summary>\n"
            "        ///     The shader resource name or caller identifier.\n"
            "        /// </summary>\n"
            "        public string ShaderName { get; }\n\n"
            "        /// <summary>\n"
            "        ///     True if the shader stream was invalid or truncated and fell back to MissingShader.\n"
            "        /// </summary>\n"
            "        public bool IsMissingShader { get; private set; }\n\n"
            "        /// <summary>\n"
            "        ///     If this shader instance owns the underlying effect and should dispose it.\n"
            "        ///     Set to false for shared effects.\n"
            "        /// </summary>\n"
            "        public bool OwnsShaderEffect { get; }\n\n"
            "        /// <summary>\n"
            "        ///     If the shader has already been disposed of.\n"
            "        /// </summary>\n"
            "        public bool IsDisposed { get; private set; }\n\n"
            "        /// <summary>\n"
            "        ///     The parameters of the shader. Takes in any type of object.\n"
            "        ///         Format: {param_name, value}\n"
            "        /// </summary>\n"
            "        public Dictionary<string, object> Parameters { get; }\n\n"
            "        /// <summary>\n"
            "        ///     Loads a shader from a byte array.\n"
            "        /// </summary>\n"
            '        /// <param name="data"></param>\n'
            '        /// <param name="parameters"></param>\n'
            "        public Shader(byte[] data, Dictionary<string, object> parameters)\n"
            "            : this(data, parameters, null)\n"
            "        {\n"
            "        }\n\n"
            "        /// <summary>\n"
            "        ///     Loads a shader from a byte array with explicit resource name diagnostics.\n"
            "        /// </summary>\n"
            '        /// <param name="data"></param>\n'
            '        /// <param name="parameters"></param>\n'
            '        /// <param name="shaderName"></param>\n'
            "        public Shader(byte[] data, Dictionary<string, object> parameters, string shaderName)\n"
            "        {\n"
            "            ShaderName = ResolveShaderName(shaderName);\n"
            "            Parameters = parameters ?? new Dictionary<string, object>();\n\n"
            "            if (data == null || data.Length < MinMgfxHeaderLength ||\n"
            "                data[0] != (byte)'M' || data[1] != (byte)'G' || data[2] != (byte)'F' || data[3] != (byte)'X')\n"
            "            {\n"
            '                FallbackToMissingShader($"Missing or invalid MGFX Effect header (length={data?.Length ?? 0}).");\n'
            "                return;\n"
            "            }\n\n"
            "            try\n"
            "            {\n"
            "                using (var stream = new MemoryStream(data, false))\n"
            "                using (var reader = new BinaryReader(stream))\n"
            "                {\n"
            "                    var signature = reader.ReadInt32();\n"
            "                    var version = reader.ReadByte();\n"
            "                    var profile = reader.ReadByte();\n"
            "                    _ = reader.ReadInt32();\n\n"
            "                    if (signature != MgfxHeaderSignature || version == 0)\n"
            "                    {\n"
            '                        FallbackToMissingShader($"Corrupted Effect header (sig=0x{signature:X8}, ver={version}, prof={profile}).");\n'
            "                        return;\n"
            "                    }\n\n"
            "                    if (version >= 10)\n"
            "                    {\n"
            "                        if (stream.Length < MinMgfxHeaderLength + 4)\n"
            "                        {\n"
            '                            FallbackToMissingShader($"Truncated MGFX v{version} shader stream (length={stream.Length}).");\n'
            "                            return;\n"
            "                        }\n\n"
            "                        stream.Seek(-4, SeekOrigin.End);\n"
            "                        var tailSignature = reader.ReadInt32();\n\n"
            "                        if (tailSignature != MgfxHeaderSignature)\n"
            "                        {\n"
            '                            FallbackToMissingShader($"Truncated MGFX v{version} tail signature (got=0x{tailSignature:X8}, length={stream.Length}).");\n'
            "                            return;\n"
            "                        }\n"
            "                    }\n"
            "                }\n\n"
            "                ShaderEffect = new Effect(GameBase.Game.GraphicsDevice, data);\n"
            "                OwnsShaderEffect = true;\n"
            "                SetParameters(false);\n"
            "            }\n"
            "            catch (EndOfStreamException ex)\n"
            "            {\n"
            '                FallbackToMissingShader($"Truncated shader stream (EndOfStreamException: {ex.Message}, length={data.Length}).");\n'
            "            }\n"
            "            catch (Exception ex)\n"
            "            {\n"
            '                FallbackToMissingShader($"Failed to load shader Effect ({ex.GetType().Name}: {ex.Message}, length={data.Length}).");\n'
            "            }\n"
            "        }\n\n"
            "        /// <summary>\n"
            "        ///     Creates a shader from a given effect.\n"
            "        /// </summary>\n"
            '        /// <param name="effect"></param>\n'
            '        /// <param name="parameters"></param>\n'
            '        /// <param name="ownsShaderEffect">Whether this shader should dispose <paramref name="effect"/>.</param>\n'
            "        public Shader(Effect effect, Dictionary<string, object> parameters, bool ownsShaderEffect = true)\n"
            "        {\n"
            "            ShaderName = ResolveShaderName(effect?.Name);\n"
            "            ShaderEffect = effect;\n"
            "            OwnsShaderEffect = ownsShaderEffect && effect != null;\n"
            "            Parameters = parameters ?? new Dictionary<string, object>();\n"
            "            if (ShaderEffect == null)\n"
            '                FallbackToMissingShader("Provided Effect instance was null.");\n'
            "            else\n"
            "                SetParameters(false);\n"
            "        }\n\n"
            "        private static string ResolveShaderName(string shaderName)\n"
            "        {\n"
            "            if (!string.IsNullOrEmpty(shaderName))\n"
            "                return shaderName;\n\n"
            "            try\n"
            "            {\n"
            "                var trace = new StackTrace(false);\n"
            "                for (var i = 0; i < trace.FrameCount; i++)\n"
            "                {\n"
            "                    var type = trace.GetFrame(i)?.GetMethod()?.DeclaringType;\n"
            "                    if (type != null && type != typeof(Shader))\n"
            "                        return type.FullName;\n"
            "                }\n"
            "            }\n"
            "            catch\n"
            "            {\n"
            "            }\n\n"
            '            return "UnknownShader";\n'
            "        }\n\n"
            "        private void FallbackToMissingShader(string reason)\n"
            "        {\n"
            "            IsMissingShader = true;\n"
            "            ShaderEffect = null;\n"
            "            var msg = $\"[{MissingShaderName}] Shader '{ShaderName}' failed to load; using {MissingShaderName} fallback. Reason: {reason}\";\n"
            "            Logger.Warning(msg, LogType.Runtime);\n"
            f"{diag_trace}"
            "        }\n\n"
            "        /// <inheritdoc />\n"
            "        /// <summary>\n"
            "        /// </summary>\n"
            "        public void Dispose()\n"
            "        {\n"
            "            if (OwnsShaderEffect)\n"
            "                ShaderEffect?.Dispose();\n\n"
            "            IsDisposed = true;\n"
            "        }\n\n"
            "        /// <summary>\n"
            "        ///     Sets all the shader parameters based on what's in the dictionary.\n"
            "        /// </summary>\n"
            "        public void SetParameters(bool setDictionaryValues)\n"
            "        {\n"
            "            if (ShaderEffect == null || Parameters == null)\n"
            "                return;\n\n"
            "            foreach (var param in Parameters)\n"
            "                SetParameter(param.Key, param.Value, setDictionaryValues);\n"
            "        }\n\n"
            "        /// <summary>\n"
            "        ///     Sets an individual parameter\n"
            "        /// </summary>\n"
            '        /// <param name="key"></param>\n'
            '        /// <param name="value"></param>\n'
            '        /// <param name="setDictionaryValue"></param>\n'
            '        /// <exception cref="InvalidTypeParameterException"></exception>\n'
            "        public void SetParameter(string key, object value, bool setDictionaryValue)\n"
            "        {\n"
            "            if (ShaderEffect == null)\n"
            "                return;\n\n"
            "            // Set the parameter in the dictionary.\n"
            "            if (setDictionaryValue)\n"
            "                Parameters[key] = value;\n\n"
            "            if (value == null || ShaderEffect.Parameters[key] == null)\n"
            "                return;\n\n"
            "            var type = value.GetType();\n\n"
            "            // Set the parameter in the shader.\n"
            "            if (type == typeof(bool))\n"
            "                ShaderEffect.Parameters[key].SetValue((bool)value);\n"
            "            else if (type == typeof(float))\n"
            "                ShaderEffect.Parameters[key].SetValue((float)value);\n"
            "            else if (type == typeof(float[]))\n"
            "                ShaderEffect.Parameters[key].SetValue((float[])value);\n"
            "            else if (type == typeof(int))\n"
            "                ShaderEffect.Parameters[key].SetValue((int)value);\n"
            "            else if (type == typeof(Texture))\n"
            "                ShaderEffect.Parameters[key].SetValue((Texture)value);\n"
            "            else if (type == typeof(Matrix))\n"
            "                ShaderEffect.Parameters[key].SetValue((Matrix)value);\n"
            "            else if (type == typeof(Matrix[]))\n"
            "                ShaderEffect.Parameters[key].SetValue((Matrix[])value);\n"
            "            else if (type == typeof(Quaternion))\n"
            "                ShaderEffect.Parameters[key].SetValue((Quaternion)value);\n"
            "            else if (type == typeof(Vector2))\n"
            "                ShaderEffect.Parameters[key].SetValue((Vector2)value);\n"
            "            else if (type == typeof(Vector2[]))\n"
            "                ShaderEffect.Parameters[key].SetValue((Vector2[])value);\n"
            "            else if (type == typeof(Vector3))\n"
            "                ShaderEffect.Parameters[key].SetValue((Vector3)value);\n"
            "            else if (type == typeof(Vector3[]))\n"
            "                ShaderEffect.Parameters[key].SetValue((Vector3[])value);\n"
            "            else if (type == typeof(Vector4))\n"
            "                ShaderEffect.Parameters[key].SetValue((Vector4)value);\n"
            "            else if (type == typeof(Vector4[]))\n"
            "                ShaderEffect.Parameters[key].SetValue((Vector4[])value);\n"
            "            else\n"
            '                throw new InvalidTypeParameterException($"ShaderEffect Parameter {key} has invalid type: {type}");\n'
            "        }\n"
            "    }\n"
            "}\n"
        )
        shader_cs.write_text(new_shader, encoding="utf-8")

for rel, res_name in (
    ("Quaver.Shared/Screens/Gameplay/UI/Health/HealthBar.cs", "Quaver.Resources/Shaders/semi-transparent.mgfxo"),
    ("Quaver.Shared/Screens/Gameplay/UI/Replays/ReplayController.cs", "Quaver.Resources/Shaders/semi-transparent.mgfxo"),
    ("Wobble/Wobble.Tests/Screens/Tests/DrawingSprites/TestDrawingSpritesScreenView.cs", "Wobble.Tests.Resources/Shaders/semi-transparent.mgfxo"),
):
    sp = root / rel
    if not sp.is_file():
        continue
    spt = sp.read_text(encoding="utf-8-sig")
    old_call = (
        '                        {"p_alpha", 0f}\n'
        "                    })"
    )
    new_call = (
        '                        {"p_alpha", 0f}\n'
        f'                    }}, "{res_name}")'
    )
    if old_call in spt and f'}}, "{res_name}")' not in spt:
        spt = spt.replace(old_call, new_call)
        sp.write_text(spt, encoding="utf-8") 
        # 9) MGFX v10 tail signature: MonoGame 3.8.1 Effect.ReadEffect espera "MGFX" (0x5846474D) al final
for mg in sorted(root.rglob("*.mgfxo")):
    data = mg.read_bytes()
    if len(data) >= 10 and data[:4] == b"MGFX" and data[4] >= 10 and not data.endswith(b"MGFX"):
        mg.write_bytes(data + b"MGFX")

# 10) SQLite WAL + transacciones en lotes para evitar 30-70s de fsyncs individuales al importar/recalcular mapas
db_mgr = root / "Quaver.Shared" / "Database" / "DatabaseManager.cs"
if db_mgr.is_file():
    dbt = db_mgr.read_text(encoding="utf-8-sig")
    old_db = "public static void Initialize() => Connection = new SQLiteConnection(DatabasePath);"
    new_db = (
        "public static void Initialize()\n"
        "        {\n"
        "            Connection = new SQLiteConnection(DatabasePath);\n"
        "            try\n"
        "            {\n"
        "                Connection.BusyTimeout = global::System.TimeSpan.FromSeconds(5);\n"
        '                Connection.ExecuteScalar<string>("PRAGMA journal_mode=WAL;");\n'
        '                Connection.Execute("PRAGMA synchronous=NORMAL;");\n'
        '                Connection.Execute("PRAGMA temp_store=MEMORY;");\n'
        '                Connection.Execute("PRAGMA cache_size=-8000;");\n'
        "            }\n"
        "            catch\n"
        "            {\n"
        "            }\n"
        "        }"
    )
    if old_db in dbt and "journal_mode=WAL" not in dbt:
        dbt = dbt.replace(old_db, new_db)
        db_mgr.write_text(dbt, encoding="utf-8")

map_cache = root / "Quaver.Shared" / "Database" / "Maps" / "MapDatabaseCache.cs"
if map_cache.is_file():
    mct = map_cache.read_text(encoding="utf-8-sig")
    old_anc = (
        '            ImportProgressEventArgs.Report(progress, "Importing New Maps", $"Checking {files.Count} files for uncached maps", 0, files.Count, false);\n\n'
        "            for (var i = 0; i < files.Count; i++)\n"
        "            {\n"
        "                var file = files[i];\n\n"
        "                if (hashset.Contains(BackslashToForward(file)))\n"
        "                {\n"
        '                    ImportProgressEventArgs.Report(progress, "Importing New Maps", $"Skipping {Path.GetFileName(file)}", i + 1, files.Count);\n\n'
        "                    continue;\n"
        "                }\n\n"
        "                // Found map that isn't cached in the database yet.\n"
        "                try\n"
        "                {\n"
        "                    var map = Map.FromQua(Qua.Parse(file, false), file);\n"
        "                    InsertMap(map);\n\n"
        "                    if (!QuaverSettingsDatabaseCache.OutdatedMaps.Contains(map))\n"
        "                        QuaverSettingsDatabaseCache.OutdatedMaps.Add(map);\n"
        "                }\n"
        "                catch (Exception e)\n"
        "                {\n"
        "                    Logger.Error(e, LogType.Runtime);\n"
        "                }\n\n"
        '                ImportProgressEventArgs.Report(progress, "Importing New Maps", $"Importing {Path.GetFileName(file)}", i + 1, files.Count);\n'
        "            }"
    )
    new_anc = (
        '            ImportProgressEventArgs.Report(progress, "Importing New Maps", $"Checking {files.Count} files for uncached maps", 0, files.Count, false);\n\n'
        "            DatabaseManager.Connection.RunInTransaction(() =>\n"
        "            {\n"
        "                for (var i = 0; i < files.Count; i++)\n"
        "                {\n"
        "                    var file = files[i];\n\n"
        "                    if (hashset.Contains(BackslashToForward(file)))\n"
        "                    {\n"
        '                        ImportProgressEventArgs.Report(progress, "Importing New Maps", $"Skipping {Path.GetFileName(file)}", i + 1, files.Count);\n\n'
        "                        continue;\n"
        "                    }\n\n"
        "                    // Found map that isn't cached in the database yet.\n"
        "                    try\n"
        "                    {\n"
        "                        var map = Map.FromQua(Qua.Parse(file, false), file);\n"
        "                        InsertMap(map);\n\n"
        "                        if (!QuaverSettingsDatabaseCache.OutdatedMaps.Contains(map))\n"
        "                            QuaverSettingsDatabaseCache.OutdatedMaps.Add(map);\n"
        "                    }\n"
        "                    catch (Exception e)\n"
        "                    {\n"
        "                        Logger.Error(e, LogType.Runtime);\n"
        "                    }\n\n"
        '                    ImportProgressEventArgs.Report(progress, "Importing New Maps", $"Importing {Path.GetFileName(file)}", i + 1, files.Count);\n'
        "                }\n"
        "            });"
    )
    if old_anc in mct and "RunInTransaction" not in mct:
        mct = mct.replace(old_anc, new_anc)
        map_cache.write_text(mct, encoding="utf-8")

qs_cache = root / "Quaver.Shared" / "Database" / "Settings" / "QuaverSettingsDatabaseCache.cs"
if qs_cache.is_file():
    qct = qs_cache.read_text(encoding="utf-8-sig")
    old_recalc = (
        "            for (var i = 0; i < total; i++)\n"
        "            {\n"
        "                var map = OutdatedMaps[i];\n"
        "                map.DifficultyProcessorVersion = DifficultyProcessorKeys.Version;\n\n"
        "                try\n"
        "                {\n"
        "                    map.CalculateDifficulties();\n"
        "                    MapDatabaseCache.UpdateMap(map);\n"
        "                }\n"
        "                catch (Exception e)\n"
        "                {\n"
        "                    DatabaseManager.Connection.Delete(map);\n"
        "                }\n\n"
        '                ImportProgressEventArgs.Report(progress, "Calculating Difficulties", $"Calculated {map.Artist} - {map.Title}", i + 1, total);\n'
        "            }"
    )
    new_recalc = (
        "            DatabaseManager.Connection.RunInTransaction(() =>\n"
        "            {\n"
        "                for (var i = 0; i < total; i++)\n"
        "                {\n"
        "                    var map = OutdatedMaps[i];\n"
        "                    map.DifficultyProcessorVersion = DifficultyProcessorKeys.Version;\n\n"
        "                    try\n"
        "                    {\n"
        "                        map.CalculateDifficulties();\n"
        "                        MapDatabaseCache.UpdateMap(map);\n"
        "                    }\n"
        "                    catch (Exception e)\n"
        "                    {\n"
        "                        DatabaseManager.Connection.Delete(map);\n"
        "                    }\n\n"
        '                    ImportProgressEventArgs.Report(progress, "Calculating Difficulties", $"Calculated {map.Artist} - {map.Title}", i + 1, total);\n'
        "                }\n"
        "            });"
    )
    if old_recalc in qct and "RunInTransaction" not in qct:
        qct = qct.replace(old_recalc, new_recalc)
        qs_cache.write_text(qct, encoding="utf-8")

# 12) Wobble.Platform.Utils.NativeUtils & Clipboard.NativeClipboard en Android (evitar NotImplementedException en GameplayScreen)
utils_cs = root / "Wobble" / "Wobble" / "Platform" / "Utils.cs"
if utils_cs.is_file():
    ut = utils_cs.read_text(encoding="utf-8-sig")
    if "AndroidUtils" not in ut:
        old_getter = (
            "        public static Utils NativeUtils\n"
            "        {\n"
            "            get\n"
            "            {\n"
            "                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))\n"
            "                    return new WindowsUtils();\n\n"
            "                if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))\n"
            "                    return new LinuxUtils();\n\n"
            "                if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))\n"
            "                    return new OsxUtils();\n\n"
            "                throw new NotImplementedException();\n"
            "            }\n"
            "        }"
        )
        new_getter = (
            "        private static readonly Utils _androidUtils = new AndroidUtils();\n\n"
            "        public static Utils NativeUtils\n"
            "        {\n"
            "            get\n"
            "            {\n"
            "                if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))\n"
            "                    return new WindowsUtils();\n"
            "                if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))\n"
            "                    return new LinuxUtils();\n"
            "                if (RuntimeInformation.IsOSPlatform(OSPlatform.OSX))\n"
            "                    return new OsxUtils();\n"
            "                return _androidUtils;\n"
            "            }\n"
            "        }"
        )
        old_end = (
            "        public string MimeType { get; set; }\n"
            "    }\n"
            "}"
        )
        new_end = (
            "        public string MimeType { get; set; }\n"
            "    }\n\n"
            "    internal sealed class AndroidUtils : Utils\n"
            "    {\n"
            "        public override void HighlightInFileManager(string path) { }\n"
            "        public override void OpenNatively(string path) { }\n"
            "        public override void RegisterURIScheme(string scheme, string friendlyName) { }\n"
            "        public override void RegisterFileAssociations(IReadOnlyDictionary<string, FileAssociation> associations, string applicationIconPath) { }\n"
            '        public override void ShowErrorMessage(string title, string message) => global::Wobble.Logging.Logger.Error($"[{title}] {message}", global::Wobble.Logging.LogType.Runtime);\n'
            "        public override void EnableWindowsKey() { }\n"
            "        public override void DisableWindowsKey() { }\n"
            "    }\n"
            "}"
        )
        if old_getter in ut and old_end in ut:
            ut = ut.replace(old_getter, new_getter).replace(old_end, new_end)
            utils_cs.write_text(ut, encoding="utf-8")

clip_cs = root / "Wobble" / "Wobble" / "Platform" / "Clipboard.cs"
if clip_cs.is_file():
    ct = clip_cs.read_text(encoding="utf-8-sig")
    if "AndroidClipboard" not in ct:
        old_c_ret = "                return null;"
        new_c_ret = "                return _androidClipboard;"
        old_c_top = "        public static Clipboard NativeClipboard"
        new_c_top = "        private static readonly Clipboard _androidClipboard = new AndroidClipboard();\n\n        public static Clipboard NativeClipboard"
        old_c_end = (
            "        public abstract void SetText(string selectedText);\n"
            "    }\n"
            "}"
        )
        new_c_end = (
            "        public abstract void SetText(string selectedText);\n"
            "    }\n\n"
            "    internal sealed class AndroidClipboard : Clipboard\n"
            "    {\n"
            '        private string _text = "";\n'
            "        public override string GetText() => _text;\n"
            '        public override void SetText(string selectedText) => _text = selectedText ?? "";\n'
            "    }\n"
            "}"
        )
        if old_c_top in ct and old_c_ret in ct and old_c_end in ct:
            ct = ct.replace(old_c_top, new_c_top).replace(old_c_ret, new_c_ret).replace(old_c_end, new_c_end)
            clip_cs.write_text(ct, encoding="utf-8")

# 13) QuaverGame.Update / Draw: capturar excepciones sin colgar SyncContext.Send (evita ANR "Quaver no responde")
qg_cs = root / "Quaver.Shared" / "QuaverGame.cs"
if qg_cs.is_file():
    qgt = qg_cs.read_text(encoding="utf-8-sig")
    has_diag_qg = (root / "Wobble" / "Wobble" / "Logging" / "AndroidDiagnostics.cs").is_file()
    if "_androidFatalStopped" not in qgt and has_diag_qg:
        old_upd = (
            "        protected override void Update(GameTime gameTime)\n"
            "        {\n"
            "            if (!IsReadyToUpdate)\n"
            "                return;"
        )
        new_upd = (
            "        private bool _androidFatalStopped;\n\n"
            "        protected override void Update(GameTime gameTime)\n"
            "        {\n"
            "            if (_androidFatalStopped || !IsReadyToUpdate)\n"
            "                return;\n"
            "            try\n"
            "            {"
        )
        old_upd_end_android = (
            "            if (!global::System.OperatingSystem.IsAndroid())\n"
            "                Window.AllowUserResizing = QuaverWindowManager.CanChangeResolutionOnScene;\n"
            "        }"
        )
        old_upd_end_plain = (
            "            Window.AllowUserResizing = QuaverWindowManager.CanChangeResolutionOnScene;\n"
            "        }"
        )
        new_upd_end_tail = (
            "            }\n"
            "            catch (Exception ex)\n"
            "            {\n"
            "                _androidFatalStopped = true;\n"
            '                global::Wobble.Logging.AndroidDiagnostics.Fatal("QuaverGame.Update", ex);\n'
            "            }\n"
            "        }"
        )
        old_drw = (
            "        protected override void Draw(GameTime gameTime)\n"
            "        {\n"
            "            if (!IsReadyToUpdate)\n"
            "                return;"
        )
        new_drw = (
            "        protected override void Draw(GameTime gameTime)\n"
            "        {\n"
            "            if (_androidFatalStopped || !IsReadyToUpdate)\n"
            "                return;\n"
            "            try\n"
            "            {"
        )
        old_drw_end = (
            "            ClearAlphaChannel(gameTime);\n"
            "        }"
        )
        new_drw_end = (
            "            ClearAlphaChannel(gameTime);\n"
            "            }\n"
            "            catch (Exception ex)\n"
            "            {\n"
            "                _androidFatalStopped = true;\n"
            '                global::Wobble.Logging.AndroidDiagnostics.Fatal("QuaverGame.Draw", ex);\n'
            "            }\n"
            "        }"
        )
        if old_upd in qgt and old_drw in qgt and old_drw_end in qgt and (old_upd_end_android in qgt or old_upd_end_plain in qgt):
            qgt = qgt.replace(old_upd, new_upd, 1)
            if old_upd_end_android in qgt:
                qgt = qgt.replace(old_upd_end_android, "            if (!global::System.OperatingSystem.IsAndroid())\n                Window.AllowUserResizing = QuaverWindowManager.CanChangeResolutionOnScene;\n" + new_upd_end_tail, 1)
            else:
                qgt = qgt.replace(old_upd_end_plain, "            Window.AllowUserResizing = QuaverWindowManager.CanChangeResolutionOnScene;\n" + new_upd_end_tail, 1)
            qgt = qgt.replace(old_drw, new_drw, 1).replace(old_drw_end, new_drw_end, 1)
            qg_cs.write_text(qgt, encoding="utf-8")
            # 14) Dependencia NuGet SteamKit2 3.5.0 en Quaver.Shared.csproj (para Auth Steam + Workshop API/CDN sin libsteam_api.so)
qs_csproj = root / "Quaver.Shared" / "Quaver.Shared.csproj"
if qs_csproj.is_file():
    qct = qs_csproj.read_text(encoding="utf-8-sig")
    if 'Include="SteamKit2"' not in qct:
        anchor = '    <PackageReference Include="WilliamQiufeng.SearchParser" Version="0.2.6-beta.1" />'
        if anchor in qct:
            qct = qct.replace(
                anchor,
                anchor + '\n    <PackageReference Include="SteamKit2" Version="3.5.0" />',
                1,
            )
            qs_csproj.write_text(qct, encoding="utf-8")

# 15) Wobble AndroidPlatformBridge (OpenUrlHandler, PromptTextHandler, Clipboard) + hooks en MainActivity.cs
bridge_cs = root / "Wobble" / "Wobble" / "Platform" / "AndroidPlatformBridge.cs"
if bridge_cs.parent.is_dir():
    if not bridge_cs.is_file():
        bridge_cs.write_text(
            """using System;

namespace Wobble.Platform
{
    public static class AndroidPlatformBridge
    {
        public static bool HasVibrator { get; set; }
        public static Action<int, int> VibrateHandler { get; set; }
        public static float SafeInsetLeft { get; set; }
        public static float SafeInsetTop { get; set; }
        public static float SafeInsetRight { get; set; }
        public static float SafeInsetBottom { get; set; }
        public static Microsoft.Xna.Framework.Input.Touch.TouchLocation[] CurrentTouchSnapshot { get; private set; }
            = Array.Empty<Microsoft.Xna.Framework.Input.Touch.TouchLocation>();

        public static Action OnAfterTouchSnapshotUpdated { get; set; }
        public static bool SuppressMouseFromTouch { get; set; }
        public static Func<Microsoft.Xna.Framework.Input.Keys[]> GetMenuNavVirtualKeysHandler { get; set; }
        public static volatile bool IsNativeBackPressed;

        public static Action<int, bool> OnNativeGamepadButton { get; set; }
        public static Action<float, float, float, float, float, float> OnNativeGamepadAxes { get; set; }
        public static Action<string, bool> OnNativeGamepadConnectionChanged { get; set; }
        public static string ConnectedGamepadName { get; private set; } = string.Empty;

        public static void UpdateTouchSnapshot(Microsoft.Xna.Framework.Input.Touch.TouchCollection touches)
        {
            if (touches.Count == 0)
            {
                if (CurrentTouchSnapshot.Length != 0)
                    CurrentTouchSnapshot = Array.Empty<Microsoft.Xna.Framework.Input.Touch.TouchLocation>();
            }
            else
            {
                var arr = new Microsoft.Xna.Framework.Input.Touch.TouchLocation[touches.Count];
                for (var i = 0; i < touches.Count; i++)
                    arr[i] = touches[i];
                CurrentTouchSnapshot = arr;
            }
            try { OnAfterTouchSnapshotUpdated?.Invoke(); } catch { }
        }

        public static void NotifyNativeGamepadButton(int keyCode, bool isDown)
        {
            try { OnNativeGamepadButton?.Invoke(keyCode, isDown); } catch { }
        }

        public static void NotifyNativeGamepadAxes(float lx, float ly, float hx, float hy, float lt, float rt)
        {
            try { OnNativeGamepadAxes?.Invoke(lx, ly, hx, hy, lt, rt); } catch { }
        }

        public static void NotifyGamepadConnection(string name, bool connected)
        {
            ConnectedGamepadName = connected ? (name ?? "Gamepad") : string.Empty;
            try { OnNativeGamepadConnectionChanged?.Invoke(name ?? "Gamepad", connected); } catch { }
        }

        public static void Vibrate(int durationMs, int amplitude)
        {
            try { VibrateHandler?.Invoke(durationMs, Math.Clamp(amplitude, 1, 255)); } catch { }
        }
        public static Action<string> OpenUrlHandler { get; set; }
        public static Action<string, string, bool, Action<string>> PromptTextHandler { get; set; }
        public static Action<string> CopyTextHandler { get; set; }
        public static Func<string> PasteTextHandler { get; set; }
    }
}
""",
            encoding="utf-8",
        )
    else:
        bt = bridge_cs.read_text(encoding="utf-8-sig")
        if "OpenUrlHandler" not in bt:
            bt = bt.replace(
                "    }\n}",
                "        public static Action<string> OpenUrlHandler { get; set; }\n"
                "        public static Action<string, string, bool, Action<string>> PromptTextHandler { get; set; }\n"
                "        public static Action<string> CopyTextHandler { get; set; }\n"
                "        public static Func<string> PasteTextHandler { get; set; }\n"
                "    }\n}",
                1,
            )
            bridge_cs.write_text(bt, encoding="utf-8")

if ma.is_file():
    mat = ma.read_text(encoding="utf-8-sig")
    if "InitWorkshopPlatformBridge" not in mat:
        old_init_call = "            InitHaptics();"
        new_init_call = "            InitHaptics();\n            InitWorkshopPlatformBridge();"
        old_end_cls = "        private void InitHaptics()"
        new_method = """        private void InitWorkshopPlatformBridge()
        {
            AndroidPlatformBridge.OpenUrlHandler = url =>
            {
                if (string.IsNullOrWhiteSpace(url))
                    return;

                RunOnUiThread(() =>
                {
                    try
                    {
                        var uri = global::Android.Net.Uri.Parse(url);
                        var intent = new Intent(Intent.ActionView, uri);
                        intent.AddFlags(ActivityFlags.NewTask);
                        StartActivity(intent);
                    }
                    catch (Exception ex)
                    {
                        AndroidDiagnostics.Trace("OpenUrlHandler ERR: " + ex.Message);
                    }
                });
            };

            AndroidPlatformBridge.CopyTextHandler = text =>
            {
                RunOnUiThread(() =>
                {
                    try
                    {
                        var cm = (ClipboardManager)GetSystemService(ClipboardService);
                        if (cm != null)
                        {
                            cm.PrimaryClip = ClipData.NewPlainText("Quaver", text ?? string.Empty);
                            Toast.MakeText(this, "Copiado al portapapeles", ToastLength.Short).Show();
                        }
                    }
                    catch (Exception ex)
                    {
                        AndroidDiagnostics.Trace("CopyTextHandler ERR: " + ex.Message);
                    }
                });
            };

            AndroidPlatformBridge.PasteTextHandler = () =>
            {
                try
                {
                    var cm = (ClipboardManager)GetSystemService(ClipboardService);
                    if (cm != null && cm.HasPrimaryClip && cm.PrimaryClip != null && cm.PrimaryClip.ItemCount > 0)
                        return cm.PrimaryClip.GetItemAt(0)?.CoerceToText(this) ?? string.Empty;
                }
                catch
                {
                }
                return string.Empty;
            };

            AndroidPlatformBridge.PromptTextHandler = (title, initialText, isPassword, onResult) =>
            {
                RunOnUiThread(() =>
                {
                    try
                    {
                        var container = new LinearLayout(this) { Orientation = Orientation.Vertical };
                        container.SetPadding(48, 24, 48, 12);

                        var input = new EditText(this)
                        {
                            Text = initialText ?? string.Empty
                        };
                        input.SetSingleLine(true);
                        input.InputType = isPassword
                            ? global::Android.Text.InputTypes.ClassText | global::Android.Text.InputTypes.TextVariationPassword
                            : global::Android.Text.InputTypes.ClassText | global::Android.Text.InputTypes.TextFlagNoSuggestions;
                        if (!string.IsNullOrEmpty(input.Text))
                            input.SetSelection(input.Text.Length);

                        container.AddView(input);

                        var dlg = new AlertDialog.Builder(this)
                            .SetTitle(string.IsNullOrEmpty(title) ? "Introducir texto" : title)
                            .SetView(container)
                            .SetPositiveButton("Aceptar", (s, e) =>
                            {
                                var val = input.Text ?? string.Empty;
                                onResult?.Invoke(val);
                            })
                            .SetNegativeButton("Cancelar", (s, e) => onResult?.Invoke(null))
                            .SetCancelable(false)
                            .Create(); 
                            
                        dlg.Window?.SetSoftInputMode(SoftInput.StateVisible);
                        dlg.Show();
                        input.RequestFocus();
                    }
                    catch (Exception ex)
                    {
                        AndroidDiagnostics.Trace("PromptTextHandler ERR: " + ex.Message);
                    }
                });
            };
        }

        private void InitHaptics()"""
        if old_init_call in mat and old_end_cls in mat:
            mat = mat.replace(old_init_call, new_init_call, 1).replace(old_end_cls, new_method, 1)
            ma.write_text(mat, encoding="utf-8")

# 16) BrowserHelper.OpenURL & OnlineManager.Login seguros en Android
bh_cs = root / "Quaver.Shared" / "Helpers" / "BrowserHelper.cs"
if bh_cs.is_file():
    bht = bh_cs.read_text(encoding="utf-8-sig")
    if "AndroidPlatformBridge.OpenUrlHandler" not in bht:
        bht = bht.replace(
            "using Steamworks;",
            "using Quaver.Shared.Online;\nusing Steamworks;\nusing Wobble.Platform;",
            1,
        )
        old_open = (
            "        public static void OpenURL(string url, bool forceNormalBrowser = false)\n"
            "        {\n"
            "            if (!forceNormalBrowser && SteamUtils.IsOverlayEnabled())"
        )
        new_open = (
            "        public static void OpenURL(string url, bool forceNormalBrowser = false)\n"
            "        {\n"
            "            if (string.IsNullOrWhiteSpace(url))\n"
            "                return;\n\n"
            "            if (global::System.OperatingSystem.IsAndroid())\n"
            "            {\n"
            "                try { AndroidPlatformBridge.OpenUrlHandler?.Invoke(url); } catch { }\n"
            "                return;\n"
            "            }\n\n"
            "            if (!forceNormalBrowser && SteamManager.IsInitialized && SteamUtils.IsOverlayEnabled())"
        )
        if old_open in bht:
            bht = bht.replace(old_open, new_open, 1)
            bh_cs.write_text(bht, encoding="utf-8")

om_cs = root / "Quaver.Shared" / "Online" / "OnlineManager.cs"
if om_cs.is_file():
    omt = om_cs.read_text(encoding="utf-8-sig")
    old_om = "Client.Connect(SteamUser.GetSteamID().m_SteamID, SteamFriends.GetPersonaName(), false);"
    new_om = "Client.Connect(SteamManager.GetSteamIdOrZero(), SteamManager.GetPersonaNameOrDefault(), false);"
    if old_om in omt:
        omt = omt.replace(old_om, new_om, 1)
        om_cs.write_text(omt, encoding="utf-8")

# 17) QuaverScreenType.Workshop y enlaces de menú (V1 MainMenu, V2 MainMenu, IconTextButtonSkins)
qst_cs = root / "Quaver.Shared" / "Screens" / "QuaverScreenType.cs"
if qst_cs.is_file():
    qstt = qst_cs.read_text(encoding="utf-8-sig")
    if "Workshop" not in qstt:
        qstt = qstt.replace("        Initialization\n", "        Initialization,\n        Workshop\n", 1)
        qst_cs.write_text(qstt, encoding="utf-8")

mmv_cs = root / "Quaver.Shared" / "Screens" / "Main" / "MainMenuScreenView.cs"
if mmv_cs.is_file():
    mmvt = mmv_cs.read_text(encoding="utf-8-sig")
    if "SteamWorkshopScreen" not in mmvt:
        mmvt = mmvt.replace(
            "using Quaver.Shared.Screens.Options;",
            "using Quaver.Shared.Screens.Options;\nusing Quaver.Shared.Screens.Workshop;",
            1,
        )
        old_ws_btn = (
            "                new NavigationButton(FontAwesome.Get(FontAwesomeIcon.fa_open_wrench_tool_silhouette), LocalizationManager.Get(NavigationButtonKeys[4]),\n"
            '                    (sender, args) => BrowserHelper.OpenURL($"https://steamcommunity.com/app/{SteamManager.ApplicationId}/workshop/")),'
        )
        new_ws_btn = (
            "                new NavigationButton(FontAwesome.Get(FontAwesomeIcon.fa_open_wrench_tool_silhouette), LocalizationManager.Get(NavigationButtonKeys[4]),\n"
            "                    (sender, args) => screen?.Exit(() => new SteamWorkshopScreen())),"
        )
        if old_ws_btn in mmvt:
            mmvt = mmvt.replace(old_ws_btn, new_ws_btn, 1)
            mmv_cs.write_text(mmvt, encoding="utf-8")

mmv2_cs = root / "Quaver.Shared" / "Screens" / "V2" / "Main" / "MainMenuScreenView.cs"
if mmv2_cs.is_file():
    mmv2t = mmv2_cs.read_text(encoding="utf-8-sig")
    if "SteamWorkshopScreen" not in mmv2t:
        old_v2_dl = (
            '            CreateAction(GlobalIcons.Get(GlobalIcon.Download), "Screen_Main_DownloadSongs",\n'
            "                screen.ExitToDownload);"
        )
        new_v2_dl = (
            old_v2_dl + "\n"
            '            CreateAction(GlobalIcons.Get(GlobalIcon.Workshop), "Screen_Main_SteamWorkshop",\n'
            "                () => screen.Exit(() => new global::Quaver.Shared.Screens.Workshop.SteamWorkshopScreen()));"
        )
        if old_v2_dl in mmv2t:
            mmv2t = mmv2t.replace(old_v2_dl, new_v2_dl, 1)
            mmv2_cs.write_text(mmv2t, encoding="utf-8")

ibs_cs = root / "Quaver.Shared" / "Graphics" / "Menu" / "Border" / "Components" / "Buttons" / "IconTextButtonSkins.cs"
if ibs_cs.is_file():
    ibst = ibs_cs.read_text(encoding="utf-8-sig")
    if "SteamWorkshopScreen" not in ibst:
        old_ibs = 'BrowserHelper.OpenURL($"https://steamcommunity.com/app/{SteamManager.ApplicationId}/workshop/");'
        new_ibs = (
            "var game = Wobble.GameBase.Game as global::Quaver.Shared.QuaverGame;\n"
            "                if (game?.CurrentScreen != null && !game.CurrentScreen.Exiting)\n"
            "                    game.CurrentScreen.Exit(() => new global::Quaver.Shared.Screens.Workshop.SteamWorkshopScreen());"
        )
        if old_ibs in ibst:
            ibst = ibst.replace(old_ibs, new_ibs, 1)
            ibs_cs.write_text(ibst, encoding="utf-8")

# 18) SteamWorkshopService.cs: Auth SteamKit2 (Credenciales/2FA/QR + RefreshToken) + PublishedFile RPC + CDN Downloader + Instalador Android
ws_dir = root / "Quaver.Shared" / "Online" / "Workshop"
ws_dir.mkdir(parents=True, exist_ok=True)
(ws_dir / "SteamWorkshopService.cs").write_text(
    r"""#nullable disable
using System;
using System.Buffers;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Net;
using System.Net.Http;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Newtonsoft.Json;
using Quaver.Shared.Config;
using Quaver.Shared.Database.Maps;
using Quaver.Shared.Skinning;
using SharpCompress.Archives;
using SharpCompress.Common;
using SteamKit2;
using SteamKit2.Authentication;
using SteamKit2.Discovery; 
using SteamKit2.CDN;
using SteamKit2.Internal;
using CdnServer = SteamKit2.CDN.Server; 
using Wobble;
using Wobble.Logging;

namespace Quaver.Shared.Online.Workshop
{
    public enum WorkshopAuthState
    {
        Disconnected,
        Connecting,
        Anonymous,
        AwaitingCredentialsGuard,
        AwaitingQrApproval,
        Authenticated,
        Failed
    }

    public enum WorkshopBrowseMode
    {
        All,
        Skins,
        Plugins,
        Collections,
        MySubscriptions,
        MyFiles,
        Installed
    }

    public enum WorkshopSortMode
    {
        Trending,
        MostSubscribed,
        TopRated,
        Newest,
        RecentlyUpdated
    }

    public class SteamSessionData
    {
        public string AccountName { get; set; }
        public ulong SteamId { get; set; }
        public string RefreshToken { get; set; }
        public string GuardData { get; set; }
    }

    public class WorkshopLocalMeta
    {
        public ulong PublishedFileId { get; set; }
        public string Title { get; set; }
        public string Category { get; set; }
        public string InstallPath { get; set; }
        public uint TimeUpdated { get; set; }
        public DateTime InstalledAtUtc { get; set; }
        public bool HasSkin { get; set; }
        public bool HasMaps { get; set; }
    }

    public class WorkshopItemInfo
    {
        public ulong PublishedFileId { get; set; }
        public ulong CreatorSteamId { get; set; }
        public string Title { get; set; } = string.Empty;
        public string ShortDescription { get; set; } = string.Empty;
        public string PreviewUrl { get; set; } = string.Empty;
        public string FileUrl { get; set; } = string.Empty;
        public ulong HContentFile { get; set; }
        public string FileName { get; set; } = string.Empty;
        public ulong FileSize { get; set; }
        public uint FileType { get; set; }
        public uint Subscriptions { get; set; }
        public uint Views { get; set; }
        public uint TimeUpdated { get; set; }
        public float VoteScore { get; set; }
        public List<string> Tags { get; set; } = new List<string>();
        public List<ulong> ChildrenIds { get; set; } = new List<ulong>();
        public bool IsInstalled { get; set; }
        public string LocalInstallPath { get; set; }
        public string InstalledCategory { get; set; }
        public bool InstalledHasSkin { get; set; }
    }

    public class WorkshopQueryResult
    {
        public List<WorkshopItemInfo> Items { get; set; } = new List<WorkshopItemInfo>();
        public uint Total { get; set; }
        public bool HasMore { get; set; }
        public string Notice { get; set; }
    }

    public class WorkshopInstallResult
    {
        public bool Success { get; set; }
        public string Message { get; set; } = string.Empty;
        public string InstallPath { get; set; } = string.Empty;
        public string Category { get; set; } = string.Empty;
        public bool HasSkin { get; set; }
        public bool QueuedMaps { get; set; }
        public ulong PrimaryId { get; set; }
    }
    internal sealed class AndroidMachineInfoProvider : IMachineInfoProvider
    {
        private readonly string _idFilePath;
        private readonly byte[] _cachedId;

        public AndroidMachineInfoProvider(string stateDir)
        {
            try
            {
                Directory.CreateDirectory(stateDir);
                _idFilePath = Path.Combine(stateDir, "steam-machine-id.bin");
                if (File.Exists(_idFilePath))
                {
                    var bytes = File.ReadAllBytes(_idFilePath);
                    if (bytes != null && bytes.Length >= 16)
                    {
                        _cachedId = bytes;
                        return;
                    }
                }

                var guid = Guid.NewGuid().ToByteArray();
                _cachedId = guid;
                File.WriteAllBytes(_idFilePath, guid);
            }
            catch
            {
                _cachedId = Guid.NewGuid().ToByteArray();
            }
        }

        public byte[] GetMachineGuid() => _cachedId;
        public byte[] GetMacAddress() => _cachedId;
        public byte[] GetDiskId() => _cachedId;
    }

    public sealed class InteractiveSteamAuthenticator : IAuthenticator
    {
        private readonly Func<bool, Task<string>> _deviceCodeProvider;
        private readonly Func<string, bool, Task<string>> _emailCodeProvider;
        private readonly Func<Task<bool>> _deviceConfirmationProvider;

        public InteractiveSteamAuthenticator(
            Func<bool, Task<string>> deviceCodeProvider,
            Func<string, bool, Task<string>> emailCodeProvider,
            Func<Task<bool>> deviceConfirmationProvider)
        {
            _deviceCodeProvider = deviceCodeProvider;
            _emailCodeProvider = emailCodeProvider;
            _deviceConfirmationProvider = deviceConfirmationProvider;
        }

        public Task<string> GetDeviceCodeAsync(bool previousCodeWasIncorrect)
            => _deviceCodeProvider != null
                ? _deviceCodeProvider(previousCodeWasIncorrect)
                : Task.FromResult(string.Empty);

        public Task<string> GetEmailCodeAsync(string email, bool previousCodeWasIncorrect)
            => _emailCodeProvider != null
                ? _emailCodeProvider(email ?? string.Empty, previousCodeWasIncorrect)
                : Task.FromResult(string.Empty);

        public Task<bool> AcceptDeviceConfirmationAsync()
            => _deviceConfirmationProvider != null
                ? _deviceConfirmationProvider()
                : Task.FromResult(true);
    }

    public sealed class SteamWorkshopService
    {
        public const uint QuaverAppId = 980610;
        public const uint QuaverWorkshopDepotId = 980610;

        public static SteamWorkshopService Instance { get; } = new SteamWorkshopService();

        private readonly SemaphoreSlim _connLock = new SemaphoreSlim(1, 1);
        private readonly ConcurrentDictionary<uint, byte[]> _depotKeys = new ConcurrentDictionary<uint, byte[]>();
        private readonly ConcurrentDictionary<(uint depotId, string host), string> _cdnTokens = new ConcurrentDictionary<(uint, string), string>();
        private readonly HttpClient _http = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };

        private SteamClient _client;
        private CallbackManager _callbacks;
        private SteamUser _steamUser;
        private SteamApps _steamApps;
        private SteamContent _steamContent;
        private PublishedFile _publishedFile;

        private Thread _callbackThread;
        private CancellationTokenSource _pumpCts;
        private long _clientEpoch;
        private string _lastDebugLog = string.Empty;
        private SteamConfiguration _steamConfig; 
        private TaskCompletionSource<bool> _connectedTcs;
        private TaskCompletionSource<SteamUser.LoggedOnCallback> _loggedOnTcs;
        private bool _freeLicenseRequested;
        private static bool _debugLogHooked; 

        public WorkshopAuthState AuthState { get; private set; } = WorkshopAuthState.Disconnected;
        public string AccountName { get; private set; } = string.Empty;
        public ulong AuthenticatedSteamId { get; private set; }
        public string LastAuthMessage { get; private set; } = string.Empty;
        public bool IsAuthenticated => AuthState == WorkshopAuthState.Authenticated && AuthenticatedSteamId != 0;

        public event Action AuthStateChanged;

        private SteamSessionData _savedSession;

        private SteamWorkshopService()
        {
            _http.DefaultRequestHeaders.UserAgent.ParseAdd("QuaverAndroid-Workshop/1.0");
            if (!_debugLogHooked)
            {
                _debugLogHooked = true;
                try
                {
                    DebugLog.Enabled = true;
                    DebugLog.AddListener((cat, msg) =>
                    {
                        var line = $"[SteamKit2:{cat}] {msg}";
                        _lastDebugLog = line;
                        Logger.Debug(line, LogType.Network);
                    });
                }
                catch { }
            } 
            LoadSessionFromDisk();
        }
        private SteamConfiguration GetOrCreateSteamConfig(ProtocolTypes protocols)
        {
            var baseDir = Path.GetDirectoryName(GetSessionFilePath()) ?? GetWorkshopRootDir();
            var serversFile = Path.Combine(baseDir, "steam-cm-servers.bin");
            if (_steamConfig == null || _steamConfig.ProtocolTypes != protocols)
            {
                _steamConfig = SteamConfiguration.Create(b => b
                    .WithProtocolTypes(protocols)
                    .WithConnectionTimeout(TimeSpan.FromSeconds(15))
                    .WithDirectoryFetch(true)
                    .WithServerListProvider(new FileStorageServerListProvider(serversFile))
                    .WithMachineInfoProvider(new AndroidMachineInfoProvider(baseDir)));
            }
            return _steamConfig;
        }

        public static string GetSessionFilePath()
     {
         var baseDir = ConfigManager.GameDirectory?.Value;
         if (string.IsNullOrWhiteSpace(baseDir))
             baseDir = WobbleGame.WorkingDirectory;
         if (string.IsNullOrWhiteSpace(baseDir))
             baseDir = Environment.GetFolderPath(Environment.SpecialFolder.Personal);
         if (string.IsNullOrWhiteSpace(baseDir))
             baseDir = Directory.GetCurrentDirectory();
         Directory.CreateDirectory(baseDir);
         return Path.Combine(baseDir, "steam-session.json");
     } 

        public static string GetWorkshopRootDir()
        {
            var dir = ConfigManager.SteamWorkshopDirectory?.Value;
            if (string.IsNullOrWhiteSpace(dir))
            {
                var baseDir = ConfigManager.GameDirectory?.Value ?? WobbleGame.WorkingDirectory ?? Directory.GetCurrentDirectory();
                dir = Path.Combine(baseDir, "Workshop");
            }
            Directory.CreateDirectory(dir);
            return dir;
        }

        public static string GetSongsDir()
        {
            var dir = ConfigManager.SongDirectory?.Value;
            if (string.IsNullOrWhiteSpace(dir))
            {
                var baseDir = ConfigManager.GameDirectory?.Value ?? WobbleGame.WorkingDirectory ?? Directory.GetCurrentDirectory();
                dir = Path.Combine(baseDir, "Songs");
            }
            Directory.CreateDirectory(dir);
            return dir;
        }

        public bool HasSavedSession() => _savedSession != null && !string.IsNullOrEmpty(_savedSession.RefreshToken);

        private void LoadSessionFromDisk()
        {
            try
            {
                var path = GetSessionFilePath();
                if (!File.Exists(path))
                    return;
                _savedSession = JsonConvert.DeserializeObject<SteamSessionData>(File.ReadAllText(path));
                if (_savedSession != null && !string.IsNullOrEmpty(_savedSession.AccountName))
                    AccountName = _savedSession.AccountName;
            }
            catch (Exception ex)
            {
                Logger.Warning("No se pudo leer steam-session.json: " + ex.Message, LogType.Network);
            }
        }

        private void SaveSessionToDisk(SteamSessionData data)
        {
            _savedSession = data;
            try
            {
                var path = GetSessionFilePath();
                File.WriteAllText(path, JsonConvert.SerializeObject(data, Formatting.Indented));
            }
            catch (Exception ex)
            {
                Logger.Warning("No se pudo guardar steam-session.json: " + ex.Message, LogType.Network);
            }
        }

        private void ResetClientUnsafe(ProtocolTypes protocols = ProtocolTypes.WebSocket | ProtocolTypes.Tcp)
        {
            var epoch = Interlocked.Increment(ref _clientEpoch);
            _connectedTcs = null;
            _loggedOnTcs = null;

            var oldCts = _pumpCts;
            _pumpCts = new CancellationTokenSource();
            var localCts = _pumpCts;
            try { oldCts?.Cancel(); } catch { }

            var oldClient = _client;
            try { oldClient?.Disconnect(); } catch { }

            var cfg = GetOrCreateSteamConfig(protocols);
            var client = new SteamClient(cfg);
            var callbacks = new CallbackManager(client);

            _client = client;
            _callbacks = callbacks;
            _steamUser = client.GetHandler<SteamUser>();
            _steamApps = client.GetHandler<SteamApps>();
            _steamContent = client.GetHandler<SteamContent>();
            var unified = client.GetHandler<SteamUnifiedMessages>();
            _publishedFile = unified.CreateService<PublishedFile>();

            callbacks.Subscribe<SteamClient.ConnectedCallback>(cb => OnConnected(epoch, cb));
            callbacks.Subscribe<SteamClient.DisconnectedCallback>(cb => OnDisconnected(epoch, cb));
            callbacks.Subscribe<SteamUser.LoggedOnCallback>(cb => OnLoggedOn(epoch, cb));
            callbacks.Subscribe<SteamUser.LoggedOffCallback>(cb => OnLoggedOff(epoch, cb));

            _callbackThread = new Thread(() =>
            {
                while (!localCts.IsCancellationRequested && Interlocked.Read(ref _clientEpoch) == epoch)
                {
                    try
                    {
                        callbacks.RunWaitCallbacks(TimeSpan.FromMilliseconds(150));
                    }
                    catch (Exception ex)
                    {
                        Logger.Warning("SteamKit2 callback loop: " + ex.Message, LogType.Network);
                        Thread.Sleep(200);
                    }
                }
            })
            {
                IsBackground = true,
                Name = $"SteamWorkshop-Callbacks-{epoch}"
            };
            _callbackThread.Start();
        }

        private void OnConnected(long epoch, SteamClient.ConnectedCallback cb)
        {
            if (epoch != Interlocked.Read(ref _clientEpoch))
                return;
            _connectedTcs?.TrySetResult(true);
        }

        private void OnDisconnected(long epoch, SteamClient.DisconnectedCallback cb)
        {
            if (epoch != Interlocked.Read(ref _clientEpoch))
                return;

            var detail = string.IsNullOrWhiteSpace(_lastDebugLog) ? "Desconectado de los servidores de Steam" : $"Desconectado de Steam ({_lastDebugLog})";
            _connectedTcs?.TrySetException(new IOException(detail));
            _loggedOnTcs?.TrySetException(new IOException("Desconectado durante el inicio de sesión de Steam"));

            if (!cb.UserInitiated && AuthState != WorkshopAuthState.Connecting && AuthState != WorkshopAuthState.AwaitingCredentialsGuard && AuthState != WorkshopAuthState.AwaitingQrApproval)
            {
                SetAuthState(WorkshopAuthState.Disconnected, "Conexión con Steam perdida");
            }
        }

        private void OnLoggedOn(long epoch, SteamUser.LoggedOnCallback cb)
        {
            if (epoch != Interlocked.Read(ref _clientEpoch))
                return;
            _loggedOnTcs?.TrySetResult(cb);
        }

        private void OnLoggedOff(long epoch, SteamUser.LoggedOffCallback cb)
        {
            if (epoch != Interlocked.Read(ref _clientEpoch))
                return;
            if (AuthState == WorkshopAuthState.Authenticated || AuthState == WorkshopAuthState.Anonymous)
                SetAuthState(WorkshopAuthState.Disconnected, $"Desconectado de Steam ({cb.Result})");
        }

        private async Task ConnectTransportAsync(CancellationToken ct)
        {
            Exception lastErr = null;
            var attempts = new[]
            {
                ProtocolTypes.WebSocket,
                ProtocolTypes.WebSocket,
                ProtocolTypes.WebSocket | ProtocolTypes.Tcp,
                ProtocolTypes.Tcp
            };

            for (var i = 0; i < attempts.Length; i++)
            {
                ct.ThrowIfCancellationRequested();
                try
                {
                    var prot = attempts[i];
                    var cfg = GetOrCreateSteamConfig(prot);
                    try
                    {
                        var servers = cfg.ServerList.GetAllEndPoints();
                        if (servers == null || !servers.Any(s => (s.ProtocolTypes & prot) != 0))
                            await SteamDirectory.LoadAsync(cfg, ct).ConfigureAwait(false);
                    }
                    catch { }

                    ResetClientUnsafe(prot);
                    var tcs = new TaskCompletionSource<bool>(TaskCreationOptions.RunContinuationsAsynchronously);
                    _connectedTcs = tcs;
                    _client.Connect();

                    using (var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(ct))
                    {
                        timeoutCts.CancelAfter(TimeSpan.FromSeconds(12));
                        var delayTask = Task.Delay(Timeout.Infinite, timeoutCts.Token);
                        var finished = await Task.WhenAny(tcs.Task, delayTask).ConfigureAwait(false);
                        if (finished != tcs.Task)
                            throw new TimeoutException("Tiempo de espera agotado conectando con Steam");
                        await tcs.Task.ConfigureAwait(false);
                        return;
                    }
                }
                catch (OperationCanceledException) when (ct.IsCancellationRequested)
                {
                    throw;
                }
                catch (Exception ex)
                {
                    lastErr = ex;
                    Logger.Warning($"Steam connect intento {i + 1}/{attempts.Length} fallido: {ex.Message}", LogType.Network);
                    AndroidDiagnostics.Trace($"Steam connect intento {i + 1} ({attempts[i]}) ERR: {ex.Message}");
                    if (i + 1 < attempts.Length)
                        await Task.Delay(350, ct).ConfigureAwait(false);
                }
            }

            throw lastErr ?? new IOException("No se pudo conectar con los servidores de Steam");
        } 

        private void SetAuthState(WorkshopAuthState state, string message)
        {
            AuthState = state;
            LastAuthMessage = message ?? string.Empty;
            try { AuthStateChanged?.Invoke(); } catch { }
        }
        public void SignOut()
     {
         try { _pumpCts?.Cancel(); } catch { }
         Interlocked.Increment(ref _clientEpoch);
         try { _steamUser?.LogOff(); } catch { }
         try { _client?.Disconnect(); } catch { }
         _connectedTcs = null;
         _loggedOnTcs = null;
         AccountName = string.Empty;
         AuthenticatedSteamId = 0;
         _depotKeys.Clear();
         _freeLicenseRequested = false;
         _savedSession = null;
         try
         {
             var path = GetSessionFilePath();
             if (File.Exists(path))
                 File.Delete(path);
         }
         catch { }
         SetAuthState(WorkshopAuthState.Disconnected, "Sesión cerrada");
     }
        private async Task<bool> LogOnWithTokenAsync(string accountName, string refreshToken, bool rememberSession, CancellationToken ct)
        {
            _loggedOnTcs = new TaskCompletionSource<SteamUser.LoggedOnCallback>(TaskCreationOptions.RunContinuationsAsynchronously);
            _steamUser.LogOn(new SteamUser.LogOnDetails
            {
                Username = accountName,
                AccessToken = refreshToken,
                ShouldRememberPassword = rememberSession
            });

            using (var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(ct))
            {
                timeoutCts.CancelAfter(TimeSpan.FromSeconds(18));
                var tcsTask = _loggedOnTcs.Task;
                var finished = await Task.WhenAny(tcsTask, Task.Delay(Timeout.Infinite, timeoutCts.Token)).ConfigureAwait(false);
                if (finished != tcsTask)
                    throw new TimeoutException("Tiempo de espera agotado esperando respuesta LogOn de Steam");
                var res = await tcsTask.ConfigureAwait(false);
                if (res.Result != EResult.OK)
                {
                    SetAuthState(WorkshopAuthState.Failed, $"Error de inicio de sesión: {res.Result} ({res.ExtendedResult})");
                    return false;
                }

                AccountName = accountName;
                AuthenticatedSteamId = res.ClientSteamID?.ConvertToUInt64() ?? 0;
                _depotKeys.Clear();
                _freeLicenseRequested = false;
                SetAuthState(WorkshopAuthState.Authenticated, $"Conectado como {AccountName}");
                return true;
            }
        }

        private async Task<bool> LogOnAnonymousInternalAsync(CancellationToken ct)
        {
            _loggedOnTcs = new TaskCompletionSource<SteamUser.LoggedOnCallback>(TaskCreationOptions.RunContinuationsAsynchronously);
            _steamUser.LogOnAnonymous();

            using (var timeoutCts = CancellationTokenSource.CreateLinkedTokenSource(ct))
            {
                timeoutCts.CancelAfter(TimeSpan.FromSeconds(18));
                var tcsTask = _loggedOnTcs.Task;
                var finished = await Task.WhenAny(tcsTask, Task.Delay(Timeout.Infinite, timeoutCts.Token)).ConfigureAwait(false);
                if (finished != tcsTask)
                    throw new TimeoutException("Tiempo de espera agotado en modo anónimo de Steam");
                var res = await tcsTask.ConfigureAwait(false);
                if (res.Result != EResult.OK)
                {
                    SetAuthState(WorkshopAuthState.Failed, $"No se pudo conectar en modo anónimo: {res.Result}");
                    return false;
                }

                AccountName = "Anónimo";
                AuthenticatedSteamId = 0;
                SetAuthState(WorkshopAuthState.Anonymous, "Conectado en modo público (Anónimo)");
                return true;
            }
        }

        public async Task<bool> EnsureConnectedAsync(CancellationToken ct = default)
        {
            if (_client != null && _client.IsConnected && (AuthState == WorkshopAuthState.Authenticated || AuthState == WorkshopAuthState.Anonymous))
                return true;

            await _connLock.WaitAsync(ct).ConfigureAwait(false);
            try
            {
                if (_client != null && _client.IsConnected && (AuthState == WorkshopAuthState.Authenticated || AuthState == WorkshopAuthState.Anonymous))
                    return true;

                SetAuthState(WorkshopAuthState.Connecting, "Conectando con Steam...");
                await ConnectTransportAsync(ct).ConfigureAwait(false);

                if (HasSavedSession())
                {
                    var ok = await LogOnWithTokenAsync(_savedSession.AccountName, _savedSession.RefreshToken, true, ct).ConfigureAwait(false);
                    if (ok)
                        return true;

                    SaveSessionToDisk(new SteamSessionData
                    {
                        AccountName = _savedSession.AccountName,
                        GuardData = _savedSession.GuardData
                    });
                    await ConnectTransportAsync(ct).ConfigureAwait(false);
                }

                return await LogOnAnonymousInternalAsync(ct).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                SetAuthState(WorkshopAuthState.Failed, ex.Message);
                return false;
            }
            finally
            {
                _connLock.Release();
            }
        }

        public async Task<(bool success, string message)> SignInWithCredentialsAsync(
            string username,
            string password,
            bool rememberSession,
            IAuthenticator authenticator,
            CancellationToken ct = default)
        {
            if (string.IsNullOrWhiteSpace(username) || string.IsNullOrEmpty(password))
                return (false, "Introduce usuario y contraseña de Steam.");

            await _connLock.WaitAsync(ct).ConfigureAwait(false);
            try
            {
                SetAuthState(WorkshopAuthState.Connecting, "Conectando con Steam...");
                await ConnectTransportAsync(ct).ConfigureAwait(false);

                SetAuthState(WorkshopAuthState.AwaitingCredentialsGuard, "Validando credenciales y Steam Guard...");
                var guardData = (_savedSession != null && string.Equals(_savedSession.AccountName, username.Trim(), StringComparison.OrdinalIgnoreCase))
                    ? _savedSession.GuardData
                    : null;

                var authSession = await _client.Authentication.BeginAuthSessionViaCredentialsAsync(new AuthSessionDetails
                {
                    Username = username.Trim(),
                    Password = password,
                    DeviceFriendlyName = "Quaver Android",
                    PlatformType = EAuthTokenPlatformType.k_EAuthTokenPlatformType_SteamClient,
                    WebsiteID = "Client",
                    IsPersistentSession = rememberSession,
                    GuardData = guardData,
                    Authenticator = authenticator
                }).ConfigureAwait(false);

                var pollResult = await authSession.PollingWaitForResultAsync(ct).ConfigureAwait(false);
                var ok = await LogOnWithTokenAsync(pollResult.AccountName, pollResult.RefreshToken, rememberSession, ct).ConfigureAwait(false);
                if (!ok)
                    return (false, LastAuthMessage);

                if (rememberSession)
                {
                    SaveSessionToDisk(new SteamSessionData
                    {
                        AccountName = pollResult.AccountName,
                        SteamId = AuthenticatedSteamId,
                        RefreshToken = pollResult.RefreshToken,
                        GuardData = pollResult.NewGuardData ?? guardData
                    });
                }

                return (true, $"Sesión iniciada como {pollResult.AccountName}");
            }
            catch (OperationCanceledException)
            {
                SetAuthState(WorkshopAuthState.Disconnected, "Inicio de sesión cancelado");
                return (false, "Inicio de sesión cancelado.");
            }
            catch (AuthenticationException aex)
            {
                SetAuthState(WorkshopAuthState.Failed, aex.Message);
                return (false, "Error de autenticación Steam: " + aex.Message);
            }
            catch (Exception ex)
            {
                SetAuthState(WorkshopAuthState.Failed, ex.Message);
                return (false, "Error conectando con Steam: " + ex.Message);
            }
            finally
            {
                _connLock.Release();
            }
        }

        public async Task<(bool success, string message)> StartQrSignInAsync(
            bool rememberSession,
            Action<string> onChallengeUrl,
            CancellationToken ct = default)
        {
            await _connLock.WaitAsync(ct).ConfigureAwait(false);
            try
            {
                SetAuthState(WorkshopAuthState.Connecting, "Solicitando sesión QR a Steam...");
                await ConnectTransportAsync(ct).ConfigureAwait(false);

                SetAuthState(WorkshopAuthState.AwaitingQrApproval, "Esperando aprobación en Steam Mobile App...");
                var qrSession = await _client.Authentication.BeginAuthSessionViaQRAsync(new AuthSessionDetails
                {
                    DeviceFriendlyName = "Quaver Android",
                    PlatformType = EAuthTokenPlatformType.k_EAuthTokenPlatformType_SteamClient,
                    WebsiteID = "Client",
                    IsPersistentSession = rememberSession
                }).ConfigureAwait(false);

                qrSession.ChallengeURLChanged = () =>
                {
                    try { onChallengeUrl?.Invoke(qrSession.ChallengeURL); } catch { }
                };
                onChallengeUrl?.Invoke(qrSession.ChallengeURL);

                var pollResult = await qrSession.PollingWaitForResultAsync(ct).ConfigureAwait(false);
                var ok = await LogOnWithTokenAsync(pollResult.AccountName, pollResult.RefreshToken, rememberSession, ct).ConfigureAwait(false);
                if (!ok)
                    return (false, LastAuthMessage);

                if (rememberSession)
                {
                    SaveSessionToDisk(new SteamSessionData
                    {
                        AccountName = pollResult.AccountName,
                        SteamId = AuthenticatedSteamId,
                        RefreshToken = pollResult.RefreshToken,
                        GuardData = pollResult.NewGuardData
                    });
                }

                return (true, $"Sesión iniciada como {pollResult.AccountName}");
            }
            catch (OperationCanceledException)
            {
                SetAuthState(WorkshopAuthState.Disconnected, "Sesión QR cancelada");
                return (false, "Sesión QR cancelada.");
            }
            catch (Exception ex)
            {
                SetAuthState(WorkshopAuthState.Failed, ex.Message);
                return (false, "Error en sesión QR: " + ex.Message);
            }
            finally
            {
                _connLock.Release();
            }
        }

        public async Task<bool> SwitchToAnonymousAsync(CancellationToken ct = default)
        {
            await _connLock.WaitAsync(ct).ConfigureAwait(false);
            try
            {
                SetAuthState(WorkshopAuthState.Connecting, "Conectando en modo anónimo...");
                await ConnectTransportAsync(ct).ConfigureAwait(false);
                return await LogOnAnonymousInternalAsync(ct).ConfigureAwait(false);
            }
            catch (Exception ex)
            {
                SetAuthState(WorkshopAuthState.Failed, ex.Message);
                return false;
            }
            finally
            {
                _connLock.Release();
            }
        }

        public async Task<WorkshopQueryResult> QueryWorkshopAsync(
            WorkshopBrowseMode mode,
            WorkshopSortMode sort,
            string searchText,
            int page,
            CancellationToken ct = default)
        {
            if (mode == WorkshopBrowseMode.Installed)
                return LoadLocallyInstalledItems(searchText);

            if ((mode == WorkshopBrowseMode.MySubscriptions || mode == WorkshopBrowseMode.MyFiles) && !IsAuthenticated)
            {
                var reconnected = await EnsureConnectedAsync(ct).ConfigureAwait(false);
                if (!reconnected || !IsAuthenticated)
                {
                    return new WorkshopQueryResult
                    {
                        Notice = "Inicia sesión con tu cuenta de Steam para ver tus suscripciones y archivos."
                    };
                }
            }
            else
            {
                var ok = await EnsureConnectedAsync(ct).ConfigureAwait(false);
                if (!ok)
                    return new WorkshopQueryResult { Notice = "Sin conexión a Steam. Comprueba tu red." };
            }

            var directId = TryExtractPublishedFileId(searchText);
            if (directId.HasValue)
            {
                var single = await GetDetailsAsync(new[] { directId.Value }, ct).ConfigureAwait(false);
                MarkInstalledStatus(single);
                return new WorkshopQueryResult
                {
                    Items = single,
                    Total = (uint)single.Count,
                    HasMore = false,
                    Notice = single.Count == 0 ? $"No se encontró el elemento {directId.Value}" : null
                };
            }

            if (mode == WorkshopBrowseMode.MySubscriptions || mode == WorkshopBrowseMode.MyFiles)
            {
                var req = new CPublishedFile_GetUserFiles_Request
                {
                    steamid = AuthenticatedSteamId,
                    appid = QuaverAppId,
                    page = (uint)Math.Max(1, page),
                    numperpage = 20,
                    type = mode == WorkshopBrowseMode.MySubscriptions ? "mysubscriptions" : "myfiles",
                    sortmethod = "lastupdated",
                    return_tags = true,
                    return_short_description = true,
                    return_vote_data = true,
                    return_children = true,
                    return_previews = true
                };

                var resp = await _publishedFile.GetUserFiles(req).ToTask().ConfigureAwait(false);
                if (resp.Result != EResult.OK)
                    return new WorkshopQueryResult { Notice = $"Steam API devolvió {resp.Result}" };

                var items = resp.Body.publishedfiledetails.Select(MapDetails).ToList();
                if (!string.IsNullOrWhiteSpace(searchText))
                {
                    var q = searchText.Trim();
                    items = items.Where(x =>
                        x.Title.Contains(q, StringComparison.OrdinalIgnoreCase) ||
                        x.ShortDescription.Contains(q, StringComparison.OrdinalIgnoreCase)).ToList();
                }

                MarkInstalledStatus(items);
                return new WorkshopQueryResult
                {
                    Items = items,
                    Total = resp.Body.total,
                    HasMore = (uint)(page * 20) < resp.Body.total
                };
            }

            uint queryType = sort switch
            {
                WorkshopSortMode.Trending => 3u,
                WorkshopSortMode.MostSubscribed => 9u,
                WorkshopSortMode.TopRated => 0u,
                WorkshopSortMode.Newest => 1u,
                WorkshopSortMode.RecentlyUpdated => 21u,
                _ => 3u
            };

            if (!string.IsNullOrWhiteSpace(searchText) && sort == WorkshopSortMode.Trending)
                queryType = 12u;

            var qReq = new CPublishedFile_QueryFiles_Request
            {
                query_type = queryType,
                page = (uint)Math.Max(1, page),
                numperpage = 20,
                appid = QuaverAppId,
                days = 30,
                search_text = searchText?.Trim() ?? string.Empty,
                return_tags = true,
                return_short_description = true,
                return_details = true,
                return_vote_data = true,
                return_children = true,
                return_previews = true
            };

            if (mode == WorkshopBrowseMode.Skins)
                qReq.requiredtags.Add("Skins");
            else if (mode == WorkshopBrowseMode.Plugins)
                qReq.requiredtags.Add("Plugins");
            else if (mode == WorkshopBrowseMode.Collections)
                qReq.filetype = 2u;

            var qResp = await _publishedFile.QueryFiles(qReq).ToTask().ConfigureAwait(false);
            if (qResp.Result != EResult.OK)
                return new WorkshopQueryResult { Notice = $"Steam Workshop Query error: {qResp.Result}" };

            var mapped = qResp.Body.publishedfiledetails.Select(MapDetails).ToList();
            MarkInstalledStatus(mapped);
            return new WorkshopQueryResult
            {
                Items = mapped,
                Total = qResp.Body.total,
                HasMore = (uint)(page * 20) < qResp.Body.total
            };
        }

        public async Task<List<WorkshopItemInfo>> GetDetailsAsync(IEnumerable<ulong> ids, CancellationToken ct = default)
        {
            await EnsureConnectedAsync(ct).ConfigureAwait(false);
            var req = new CPublishedFile_GetDetails_Request
            {
                appid = QuaverAppId,
                includetags = true,
                includechildren = true,
                includevotes = true,
                short_description = true,
                includemetadata = true
            };
            foreach (var id in ids)
                req.publishedfileids.Add(id);

            var resp = await _publishedFile.GetDetails(req).ToTask().ConfigureAwait(false);
            if (resp.Result != EResult.OK)
                return new List<WorkshopItemInfo>();

            return resp.Body.publishedfiledetails
                .Where(d => d.result == (uint)EResult.OK && d.publishedfileid != 0)
                .Select(MapDetails)
                .ToList();
        }

        public async Task<(bool success, string message)> SetSubscribedAsync(ulong publishedFileId, bool subscribe, CancellationToken ct = default)
        {
            if (!IsAuthenticated)
                return (false, "Necesitas iniciar sesión con tu cuenta de Steam para suscribirte.");

            if (!await EnsureConnectedAsync(ct).ConfigureAwait(false))
                return (false, "Sin conexión con Steam.");

            if (subscribe)
            {
                var res = await _publishedFile.Subscribe(new CPublishedFile_Subscribe_Request
                {
                    publishedfileid = publishedFileId,
                    appid = (int)QuaverAppId,
                    list_type = 0,
                    notify_client = true,
                    include_dependencies = true
                }).ToTask().ConfigureAwait(false);
                return res.Result == EResult.OK
                    ? (true, "Suscrito en tu cuenta de Steam")
                    : (false, $"Error suscribiendo: {res.Result}");
            }
            else
            {
                var res = await _publishedFile.Unsubscribe(new CPublishedFile_Unsubscribe_Request
                {
                    publishedfileid = publishedFileId,
                    appid = (int)QuaverAppId,
                    list_type = 0
                }).ToTask().ConfigureAwait(false);
                return res.Result == EResult.OK
                    ? (true, "Desuscrito de Steam Workshop")
                    : (false, $"Error desuscribiendo: {res.Result}");
            }
        }

        public async Task<WorkshopInstallResult> DownloadAndInstallAsync(
            WorkshopItemInfo item,
            Action<float, string> onProgress,
            CancellationToken ct = default)
        {
            if (item == null)
                return new WorkshopInstallResult { Success = false, Message = "Elemento inválido" };

            try
            {
                onProgress?.Invoke(0.02f, "Conectando con Steam3...");
                if (!await EnsureConnectedAsync(ct).ConfigureAwait(false))
                    return new WorkshopInstallResult { Success = false, Message = "No se pudo conectar con Steam." };

                var freshList = await GetDetailsAsync(new[] { item.PublishedFileId }, ct).ConfigureAwait(false);
                var target = freshList.FirstOrDefault() ?? item;

                if (target.FileType == 2 && target.ChildrenIds.Count > 0)
                {
                    var childDetails = await GetDetailsAsync(target.ChildrenIds, ct).ConfigureAwait(false);
                    var anyMaps = false;
                    var anySkin = false;
                    var doneCount = 0;

                    foreach (var child in childDetails)
                    {
                        ct.ThrowIfCancellationRequested();
                        var baseP = (float)doneCount / Math.Max(1, childDetails.Count);
                        var span = 1f / Math.Max(1, childDetails.Count);
                        var r = await DownloadSingleItemAsync(child, (p, msg) =>
                            onProgress?.Invoke(baseP + p * span, $"[{doneCount + 1}/{childDetails.Count}] {msg}"), ct).ConfigureAwait(false);

                        if (r.Success)
                        {
                            anyMaps |= r.QueuedMaps;
                            anySkin |= r.HasSkin;
                        }
                        doneCount++;
                    }

                    var colDir = Path.Combine(GetWorkshopRootDir(), target.PublishedFileId.ToString());
                    Directory.CreateDirectory(colDir);
                    WriteLocalMeta(colDir, new WorkshopLocalMeta
                    {
                        PublishedFileId = target.PublishedFileId,
                        Title = target.Title,
                        Category = "Colección",
                        InstallPath = colDir,
                        TimeUpdated = target.TimeUpdated,
                        InstalledAtUtc = DateTime.UtcNow,
                        HasSkin = anySkin,
                        HasMaps = anyMaps
                    });

                    MarkInstalledStatus(new[] { item, target });
                    return new WorkshopInstallResult
                    {
                        Success = true,
                        Message = $"Colección instalada ({doneCount} elementos)",
                        InstallPath = colDir,
                        Category = "Colección",
                        HasSkin = anySkin,
                        QueuedMaps = anyMaps,
                        PrimaryId = target.PublishedFileId
                    };
                }

                var result = await DownloadSingleItemAsync(target, onProgress, ct).ConfigureAwait(false);
                if (result.Success)
                    MarkInstalledStatus(new[] { item, target });
                return result;
            }
            catch (OperationCanceledException)
            {
                return new WorkshopInstallResult { Success = false, Message = "Descarga cancelada." };
            }
            catch (Exception ex)
            {
                Logger.Error(ex, LogType.Network);
                return new WorkshopInstallResult { Success = false, Message = "Error: " + ex.Message };
            }
        }

        private async Task<WorkshopInstallResult> DownloadSingleItemAsync(
            WorkshopItemInfo item,
            Action<float, string> onProgress,
            CancellationToken ct)
        {
            var workshopRoot = GetWorkshopRootDir();
            var stagingDir = Path.Combine(workshopRoot, ".staging", item.PublishedFileId.ToString());
            if (Directory.Exists(stagingDir))
                Directory.Delete(stagingDir, true);
            Directory.CreateDirectory(stagingDir);

            try
            {
                if (!string.IsNullOrEmpty(item.FileUrl))
                {
                    onProgress?.Invoke(0.15f, $"Descargando archivo directo ({FormatBytes(item.FileSize)})...");
                    var safeName = SanitizeFileName(string.IsNullOrWhiteSpace(item.FileName) ? $"{item.PublishedFileId}.bin" : item.FileName);
                    var rawPath = Path.Combine(stagingDir, safeName);

                    using (var resp = await _http.GetAsync(item.FileUrl, HttpCompletionOption.ResponseHeadersRead, ct).ConfigureAwait(false))
                    {
                        resp.EnsureSuccessStatusCode();
                        var total = resp.Content.Headers.ContentLength ?? (long)item.FileSize;
                        await using var remote = await resp.Content.ReadAsStreamAsync(ct).ConfigureAwait(false);
                        await using var local = File.Create(rawPath);
                        var buf = new byte[65536];
                        long readTotal = 0;
                        int n;
                        while ((n = await remote.ReadAsync(buf, 0, buf.Length, ct).ConfigureAwait(false)) > 0)
                        {
                            await local.WriteAsync(buf, 0, n, ct).ConfigureAwait(false);
                            readTotal += n;
                            if (total > 0)
                                onProgress?.Invoke(0.15f + 0.70f * Math.Min(1f, (float)readTotal / total), $"Descargando {safeName}...");
                        }
                    }

                    if (safeName.EndsWith(".zip", StringComparison.OrdinalIgnoreCase))
                    {
                        onProgress?.Invoke(0.88f, "Extrayendo archivo ZIP...");
                        ExtractArchiveToDirectory(rawPath, stagingDir);
                        File.Delete(rawPath);
                    }
                }
                else if (item.HContentFile > 0)
                {
                    await DownloadWorkshopDepotAsync(item.HContentFile, stagingDir, onProgress, ct).ConfigureAwait(false);
                }
                else
                {
                    return new WorkshopInstallResult
                    {
                        Success = false,
                        Message = "Steam no devolvió manifiesto CDN (hcontent_file) ni URL para este elemento."
                    };
                }

                onProgress?.Invoke(0.92f, "Instalando en las carpetas de Quaver Android...");
                var installed = InstallStagedContent(item, stagingDir);
                onProgress?.Invoke(1f, installed.Message);
                return installed;
            }
            finally
            {
                try
                {
                    if (Directory.Exists(stagingDir))
                        Directory.Delete(stagingDir, true);
                }
                catch
                {
                }
            }
        }

        private async Task DownloadWorkshopDepotAsync(
            ulong manifestId,
            string stagingDir,
            Action<float, string> onProgress,
            CancellationToken ct)
        {
            onProgress?.Invoke(0.05f, "Obteniendo clave del depot 980610...");
            var depotKey = await GetDepotKeyAsync(QuaverWorkshopDepotId, QuaverAppId, ct).ConfigureAwait(false);

            onProgress?.Invoke(0.08f, "Buscando servidores SteamPipe CDN...");
            var allServers = (await _steamContent.GetServersForSteamPipe().ConfigureAwait(false)).ToList();
            var servers = allServers
                .Where(s => (s.Type == "SteamCache" || s.Type == "CDN") &&
                            (s.AllowedAppIds == null || s.AllowedAppIds.Length == 0 || s.AllowedAppIds.Contains(QuaverAppId)))
                .OrderByDescending(s => s.Protocol == CdnServer.ConnectionProtocol.HTTPS) 
                .ThenBy(s => s.WeightedLoad)
                .Take(6)
                .ToList();

            if (servers.Count == 0)
                servers = allServers.Take(4).ToList();
            if (servers.Count == 0)
                throw new InvalidOperationException("No se encontraron servidores CDN de SteamPipe disponibles.");

            onProgress?.Invoke(0.12f, $"Solicitando código de manifiesto {manifestId}...");
            var requestCode = await _steamContent.GetManifestRequestCode(QuaverWorkshopDepotId, QuaverAppId, manifestId, "public").ConfigureAwait(false);
            if (requestCode == 0)
                requestCode = await _steamContent.GetManifestRequestCode(QuaverWorkshopDepotId, QuaverAppId, manifestId, string.Empty).ConfigureAwait(false);

            using var cdnClient = new global::SteamKit2.CDN.Client(_client);

            DepotManifest manifest = null;
            Exception lastManifestErr = null;
            foreach (var srv in servers)
            {
                ct.ThrowIfCancellationRequested();
                try
                {
                    _cdnTokens.TryGetValue((QuaverWorkshopDepotId, srv.Host), out var token);
                    manifest = await cdnClient.DownloadManifestAsync(
                        QuaverWorkshopDepotId,
                        manifestId,
                        requestCode,
                        srv,
                        depotKey,
                        null,
                        token).ConfigureAwait(false);
                    if (manifest != null)
                        break;
                }
                catch (SteamKitWebRequestException wex) when (wex.StatusCode == HttpStatusCode.Forbidden || wex.StatusCode == HttpStatusCode.Unauthorized)
                {
                    lastManifestErr = wex;
                    var tok = await RequestCdnAuthTokenAsync(srv).ConfigureAwait(false);
                    if (!string.IsNullOrEmpty(tok))
                    {
                        try
                        {
                            manifest = await cdnClient.DownloadManifestAsync(
                                QuaverWorkshopDepotId, manifestId, requestCode, srv, depotKey, null, tok).ConfigureAwait(false);
                            if (manifest != null)
                                break;
                        }
                        catch (Exception inner)
                        {
                            lastManifestErr = inner;
                        }
                    }
                }
                catch (Exception ex)
                {
                    lastManifestErr = ex;
                }
            }

            if (manifest == null)
                throw new InvalidOperationException("No se pudo descargar el manifiesto Workshop: " + (lastManifestErr?.Message ?? "sin servidores válidos"));

            var files = manifest.Files
                .Where(f => !f.Flags.HasFlag(EDepotFileFlag.Directory) && !string.IsNullOrEmpty(f.FileName))
                .ToList();

            ulong totalBytes = 0;
            foreach (var f in files)
                totalBytes += f.TotalSize;
            if (totalBytes == 0)
                totalBytes = 1;

            ulong downloadedBytes = 0;
            var serverIdx = 0;

            foreach (var file in files)
            {
                ct.ThrowIfCancellationRequested();
                var relPath = SanitizeRelativePath(file.FileName);
                if (string.IsNullOrEmpty(relPath))
                    continue;

                var destPath = Path.Combine(stagingDir, relPath);
                var destParent = Path.GetDirectoryName(destPath);
                if (!string.IsNullOrEmpty(destParent))
                    Directory.CreateDirectory(destParent);

                await using var fs = new FileStream(destPath, FileMode.Create, FileAccess.Write, FileShare.None);
                if (file.TotalSize > 0)
                    fs.SetLength((long)file.TotalSize);

                foreach (var chunk in file.Chunks)
                {
                    ct.ThrowIfCancellationRequested();
                    var neededSize = (int)Math.Max(chunk.UncompressedLength, chunk.CompressedLength);
                    var buffer = ArrayPool<byte>.Shared.Rent(neededSize);
                    try
                    {
                        var written = -1;
                        Exception chunkErr = null;
                        for (var attempt = 0; attempt < Math.Min(4, servers.Count); attempt++)
                        {
                            var srv = servers[(serverIdx + attempt) % servers.Count];
                            try
                            {
                                _cdnTokens.TryGetValue((QuaverWorkshopDepotId, srv.Host), out var token);
                                written = await cdnClient.DownloadDepotChunkAsync(
                                    QuaverWorkshopDepotId, chunk, srv, buffer, depotKey, null, token).ConfigureAwait(false);
                                serverIdx = (serverIdx + attempt) % servers.Count;
                                break;
                            }
                            catch (SteamKitWebRequestException wex) when (wex.StatusCode == HttpStatusCode.Forbidden || wex.StatusCode == HttpStatusCode.Unauthorized)
                            {
                                chunkErr = wex;
                                var tok = await RequestCdnAuthTokenAsync(srv).ConfigureAwait(false);
                                if (!string.IsNullOrEmpty(tok))
                                {
                                    written = await cdnClient.DownloadDepotChunkAsync(
                                        QuaverWorkshopDepotId, chunk, srv, buffer, depotKey, null, tok).ConfigureAwait(false);
                                    serverIdx = (serverIdx + attempt) % servers.Count;
                                    break;
                                }
                            }
                            catch (Exception ex)
                            {
                                chunkErr = ex;
                            }
                        }

                        if (written < 0)
                            throw new IOException($"Error descargando chunk de {relPath}: {chunkErr?.Message}");

                        fs.Seek((long)chunk.Offset, SeekOrigin.Begin);
                        await fs.WriteAsync(buffer, 0, written, ct).ConfigureAwait(false);
                        downloadedBytes += (ulong)written;

                        var pct = 0.14f + 0.76f * Math.Min(1f, (float)downloadedBytes / totalBytes);
                        onProgress?.Invoke(pct, $"Descargando {Path.GetFileName(relPath)} ({FormatBytes(downloadedBytes)} / {FormatBytes(totalBytes)})");
                    }
                    finally
                    {
                        ArrayPool<byte>.Shared.Return(buffer);
                    }
                }
            }
        }

        private async Task<byte[]> GetDepotKeyAsync(uint depotId, uint appId, CancellationToken ct)
        {
            if (_depotKeys.TryGetValue(depotId, out var cached))
                return cached;

            var keyCb = await _steamApps.GetDepotDecryptionKey(depotId, appId).ToTask().ConfigureAwait(false);
            if (keyCb.Result != EResult.OK && !_freeLicenseRequested)
            {
                _freeLicenseRequested = true;
                try
                {
                    await _steamApps.RequestFreeLicense(appId).ToTask().ConfigureAwait(false);
                    keyCb = await _steamApps.GetDepotDecryptionKey(depotId, appId).ToTask().ConfigureAwait(false);
                }
                catch
                {
                }
            }

            if (keyCb.Result != EResult.OK || keyCb.DepotKey == null || keyCb.DepotKey.Length == 0)
            {
                if (!IsAuthenticated)
                    throw new InvalidOperationException($"Steam rechazó la clave del depot ({keyCb.Result}). Inicia sesión con tu cuenta de Steam.");
                throw new InvalidOperationException($"No se pudo obtener la clave del depot {depotId}: {keyCb.Result}");
            }

            _depotKeys[depotId] = keyCb.DepotKey;
            return keyCb.DepotKey;
        }

        private async Task<string> RequestCdnAuthTokenAsync(CdnServer server)
        {
            var key = (QuaverWorkshopDepotId, server.Host);
            if (_cdnTokens.TryGetValue(key, out var existing))
                return existing;

            try
            {
                var tok = await _steamContent.GetCDNAuthToken(QuaverAppId, QuaverWorkshopDepotId, server.Host).ConfigureAwait(false); 
                if (tok.Result == EResult.OK && !string.IsNullOrEmpty(tok.Token))
                {
                    _cdnTokens[key] = tok.Token;
                    return tok.Token;
                }
            }
            catch
            {
            }
            return null;
        }

        private WorkshopInstallResult InstallStagedContent(WorkshopItemInfo item, string stagingDir)
        {
            var workshopRoot = GetWorkshopRootDir();
            var songsRoot = GetSongsDir();
            var finalWorkshopDir = Path.Combine(workshopRoot, item.PublishedFileId.ToString());

            var allFiles = Directory.GetFiles(stagingDir, "*", SearchOption.AllDirectories);

            var mapArchives = allFiles.Where(IsMapArchiveFile).ToList();
            var looseQuaFiles = allFiles.Where(f => f.EndsWith(".qua", StringComparison.OrdinalIgnoreCase)).ToList();
            var qsSkins = allFiles.Where(f => f.EndsWith(".qs", StringComparison.OrdinalIgnoreCase)).ToList();
            var skinConfigs = allFiles.Where(f =>
                string.Equals(Path.GetFileName(f), "skin.ini", StringComparison.OrdinalIgnoreCase) ||
                string.Equals(Path.GetFileName(f), "skin.yml", StringComparison.OrdinalIgnoreCase)).ToList();
            var pluginFiles = allFiles.Where(f =>
                string.Equals(Path.GetFileName(f), "settings.ini", StringComparison.OrdinalIgnoreCase)).ToList();

            var queuedMaps = false;
            var hasSkin = false;
            var category = "Recurso";
            var finalInstallPath = finalWorkshopDir;

            if (mapArchives.Count > 0 || (looseQuaFiles.Count > 0 && skinConfigs.Count == 0 && qsSkins.Count == 0))
            {
                queuedMaps = true;
                category = "Mapa";

                foreach (var archive in mapArchives)
                {
                    var dest = Path.Combine(songsRoot, $"Workshop_{item.PublishedFileId}_{Path.GetFileName(archive)}");
                    File.Copy(archive, dest, true);
                    MapsetImporter.ImportFile(dest, true);
                }

                if (looseQuaFiles.Count > 0)
                {
                    var mapFolderName = $"{SanitizeFileName(item.Title)}_{item.PublishedFileId}";
                    var songDestDir = Path.Combine(songsRoot, mapFolderName);
                    if (Directory.Exists(songDestDir))
                        Directory.Delete(songDestDir, true);
                    CopyDirectory(stagingDir, songDestDir);
                    MapsetImporter.ImportFile(songDestDir, true);
                    finalInstallPath = songDestDir;
                }
            }

            if (qsSkins.Count > 0 || skinConfigs.Count > 0)
            {
                hasSkin = true;
                category = "Skin";
                if (Directory.Exists(finalWorkshopDir))
                    Directory.Delete(finalWorkshopDir, true);
                Directory.CreateDirectory(finalWorkshopDir);

                if (qsSkins.Count > 0 && skinConfigs.Count == 0)
                {
                    ExtractArchiveToDirectory(qsSkins[0], finalWorkshopDir);
                }
                else
                {
                    var skinRoot = Path.GetDirectoryName(skinConfigs[0]) ?? stagingDir;
                    CopyDirectory(skinRoot, finalWorkshopDir);
                }
                finalInstallPath = finalWorkshopDir;
            }
            else if (pluginFiles.Count > 0)
            {
                category = "Plugin";
                if (Directory.Exists(finalWorkshopDir))
                    Directory.Delete(finalWorkshopDir, true);
                var pluginRoot = Path.GetDirectoryName(pluginFiles[0]) ?? stagingDir;
                CopyDirectory(pluginRoot, finalWorkshopDir);
                finalInstallPath = finalWorkshopDir;
            }
            else if (!queuedMaps)
            {
                if (Directory.Exists(finalWorkshopDir))
                    Directory.Delete(finalWorkshopDir, true);
                CopyDirectory(stagingDir, finalWorkshopDir);
                finalInstallPath = finalWorkshopDir;
            }

            Directory.CreateDirectory(finalWorkshopDir);
            WriteLocalMeta(finalWorkshopDir, new WorkshopLocalMeta
            {
                PublishedFileId = item.PublishedFileId,
                Title = item.Title,
                Category = category,
                InstallPath = finalInstallPath,
                TimeUpdated = item.TimeUpdated,
                InstalledAtUtc = DateTime.UtcNow,
                HasSkin = hasSkin,
                HasMaps = queuedMaps
            });

            var summary = category switch
            {
                "Skin" => $"Skin instalado en Workshop/{item.PublishedFileId}/",
                "Mapa" => "Mapa guardado en Songs/ y en cola de importación",
                "Plugin" => $"Plugin instalado en Workshop/{item.PublishedFileId}/",
                _ => $"Recurso guardado en Workshop/{item.PublishedFileId}/"
            };

            return new WorkshopInstallResult
            {
                Success = true,
                Message = summary,
                InstallPath = finalInstallPath,
                Category = category,
                HasSkin = hasSkin,
                QueuedMaps = queuedMaps,
                PrimaryId = item.PublishedFileId
            };
        }

        public bool TryApplyWorkshopSkin(ulong publishedFileId)
        {
            var dir = Path.Combine(GetWorkshopRootDir(), publishedFileId.ToString());
            if (!File.Exists(Path.Combine(dir, "skin.ini")) && !File.Exists(Path.Combine(dir, "skin.yml")))
                return false;

            ConfigManager.UseSteamWorkshopSkin.Value = true;
            ConfigManager.Skin.Value = publishedFileId.ToString();
            SkinManager.TimeSkinReloadRequested = GameBase.Game.TimeRunning;
            return true;
        }

        public bool DeleteLocalItem(ulong publishedFileId)
        {
            try
            {
                var dir = Path.Combine(GetWorkshopRootDir(), publishedFileId.ToString());
                if (Directory.Exists(dir))
                    Directory.Delete(dir, true);
                return true;
            }
            catch
            {
                return false;
            }
        }

        public async Task<byte[]> DownloadImageBytesAsync(string url, CancellationToken ct = default)
        {
            if (string.IsNullOrWhiteSpace(url))
                return null;
            try
            {
                return await _http.GetByteArrayAsync(url, ct).ConfigureAwait(false);
            }
            catch
            {
                return null;
            }
        }

        private WorkshopQueryResult LoadLocallyInstalledItems(string searchText)
        {
            var rootDir = GetWorkshopRootDir();
            var list = new List<WorkshopItemInfo>();
            if (Directory.Exists(rootDir))
            {
                foreach (var dir in Directory.GetDirectories(rootDir))
                {
                    var folderName = Path.GetFileName(dir);
                    if (!ulong.TryParse(folderName, out var id))
                        continue;

                    var meta = ReadLocalMeta(dir);
                    var hasSkin = File.Exists(Path.Combine(dir, "skin.ini")) || File.Exists(Path.Combine(dir, "skin.yml"));
                    var hasPlugin = File.Exists(Path.Combine(dir, "settings.ini"));
                    var title = meta?.Title;
                    if (string.IsNullOrWhiteSpace(title))
                        title = $"Workshop #{id}";

                    var cat = meta?.Category ?? (hasSkin ? "Skin" : hasPlugin ? "Plugin" : "Recurso");
                    var item = new WorkshopItemInfo
                    {
                        PublishedFileId = id,
                        Title = title,
                        ShortDescription = $"Instalado localmente en {meta?.InstallPath ?? dir}",
                        IsInstalled = true,
                        LocalInstallPath = meta?.InstallPath ?? dir,
                        InstalledCategory = cat,
                        InstalledHasSkin = hasSkin || (meta?.HasSkin ?? false),
                        Tags = new List<string> { cat },
                        TimeUpdated = meta?.TimeUpdated ?? 0
                    };

                    if (string.IsNullOrWhiteSpace(searchText) ||
                        item.Title.Contains(searchText.Trim(), StringComparison.OrdinalIgnoreCase) ||
                        id.ToString().Contains(searchText.Trim(), StringComparison.OrdinalIgnoreCase))
                    {
                        list.Add(item);
                    }
                }
            }

            return new WorkshopQueryResult
            {
                Items = list,
                Total = (uint)list.Count,
                HasMore = false,
                Notice = list.Count == 0 ? "Aún no tienes elementos instalados desde Steam Workshop." : null
            };
        }

        public void MarkInstalledStatus(IEnumerable<WorkshopItemInfo> items)
        {
            var rootDir = GetWorkshopRootDir();
            foreach (var item in items)
            {
                var dir = Path.Combine(rootDir, item.PublishedFileId.ToString());
                var meta = ReadLocalMeta(dir);
                var hasSkin = File.Exists(Path.Combine(dir, "skin.ini")) || File.Exists(Path.Combine(dir, "skin.yml"));
                var hasPlugin = File.Exists(Path.Combine(dir, "settings.ini"));
                item.IsInstalled = Directory.Exists(dir) && (meta != null || hasSkin || hasPlugin);
                item.InstalledHasSkin = hasSkin || (meta?.HasSkin ?? false);
                item.LocalInstallPath = meta?.InstallPath ?? (item.IsInstalled ? dir : null);
                item.InstalledCategory = meta?.Category ?? (hasSkin ? "Skin" : hasPlugin ? "Plugin" : null);
            }
        }

        private static WorkshopLocalMeta ReadLocalMeta(string dir)
        {
            try
            {
                var metaFile = Path.Combine(dir, ".workshop-meta.json");
                if (!File.Exists(metaFile))
                    return null;
                return JsonConvert.DeserializeObject<WorkshopLocalMeta>(File.ReadAllText(metaFile));
            }
            catch
            {
                return null;
            }
        }

        private static void WriteLocalMeta(string dir, WorkshopLocalMeta meta)
        {
            try
            {
                File.WriteAllText(Path.Combine(dir, ".workshop-meta.json"), JsonConvert.SerializeObject(meta, Formatting.Indented));
            }
            catch
            {
            }
        }

        private static WorkshopItemInfo MapDetails(PublishedFileDetails d) => new WorkshopItemInfo
        {
            PublishedFileId = d.publishedfileid,
            CreatorSteamId = d.creator,
            Title = string.IsNullOrWhiteSpace(d.title) ? $"Workshop #{d.publishedfileid}" : d.title,
            ShortDescription = d.short_description ?? string.Empty,
            PreviewUrl = d.preview_url ?? string.Empty,
            FileUrl = d.file_url ?? string.Empty,
            HContentFile = d.hcontent_file,
            FileName = d.filename ?? string.Empty,
            FileSize = d.file_size,
            FileType = d.file_type,
            Subscriptions = d.subscriptions,
            Views = d.views,
            TimeUpdated = d.time_updated,
            VoteScore = d.vote_data != null ? d.vote_data.score : 0f,
            Tags = d.tags.Select(t => t.tag).Where(t => !string.IsNullOrWhiteSpace(t)).ToList(),
            ChildrenIds = d.children.Select(c => c.publishedfileid).Where(id => id != 0).ToList()
        };

        private static ulong? TryExtractPublishedFileId(string input)
        {
            if (string.IsNullOrWhiteSpace(input))
                return null;
            var trimmed = input.Trim();
            if (ulong.TryParse(trimmed, out var direct) && direct > 10000)
                return direct;

            var m = Regex.Match(trimmed, @"(?:filedetails/\?id=|sharedfiles/\?id=)(\d+)");
            if (m.Success && ulong.TryParse(m.Groups[1].Value, out var urlId))
                return urlId;

            return null;
        }

        private static bool IsMapArchiveFile(string path) =>
            path.EndsWith(".qp", StringComparison.OrdinalIgnoreCase) ||
            path.EndsWith(".osz", StringComparison.OrdinalIgnoreCase) ||
            path.EndsWith(".sm", StringComparison.OrdinalIgnoreCase) ||
            path.EndsWith(".mc", StringComparison.OrdinalIgnoreCase) ||
            path.EndsWith(".mcz", StringComparison.OrdinalIgnoreCase);

        private static void ExtractArchiveToDirectory(string archivePath, string destDir)
        {
            using var archive = ArchiveFactory.Open(archivePath);
            foreach (var entry in archive.Entries)
            {
                if (!entry.IsDirectory)
                    entry.WriteToDirectory(destDir, new ExtractionOptions { ExtractFullPath = true, Overwrite = true });
            }
        }

        private static void CopyDirectory(string sourceDir, string targetDir)
        {
            Directory.CreateDirectory(targetDir);
            foreach (var file in Directory.GetFiles(sourceDir))
                File.Copy(file, Path.Combine(targetDir, Path.GetFileName(file)), true);
            foreach (var subDir in Directory.GetDirectories(sourceDir))
            {
                var name = Path.GetFileName(subDir);
                if (name == ".staging")
                    continue;
                CopyDirectory(subDir, Path.Combine(targetDir, name));
            }
        }

        private static string SanitizeRelativePath(string raw)
        {
            if (string.IsNullOrWhiteSpace(raw))
                return string.Empty;
            var normalized = raw.Replace('\\', '/').TrimStart('/');
            var parts = normalized.Split('/', StringSplitOptions.RemoveEmptyEntries)
                .Where(p => p != "." && p != "..")
                .ToArray();
            return parts.Length == 0 ? string.Empty : Path.Combine(parts);
        }

        private static string SanitizeFileName(string raw)
        {
            if (string.IsNullOrWhiteSpace(raw))
                return "workshop_item";
            var invalid = Path.GetInvalidFileNameChars();
            var cleaned = new string(raw.Select(c => invalid.Contains(c) ? '_' : c).ToArray()).Trim();
            return string.IsNullOrWhiteSpace(cleaned) ? "workshop_item" : cleaned;
        }

        public static string FormatBytes(ulong bytes)
        {
            if (bytes < 1024)
                return $"{bytes} B";
            if (bytes < 1024 * 1024)
                return $"{bytes / 1024.0:F1} KB";
            if (bytes < 1024UL * 1024 * 1024)
                return $"{bytes / (1024.0 * 1024.0):F2} MB";
            return $"{bytes / (1024.0 * 1024.0 * 1024.0):F2} GB";
        }
    }
}
""",
    encoding="utf-8",
)

# 19) UI de Steam Auth (SteamAuthDialog.cs) y Navegador/Descargador Workshop (SteamWorkshopScreen.cs + SteamWorkshopScreenView.cs)
wui_dir = root / "Quaver.Shared" / "Screens" / "Workshop"
wui_dir.mkdir(parents=True, exist_ok=True)

(wui_dir / "SteamAuthDialog.cs").write_text(
    r"""#nullable disable
using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Quaver.Shared.Assets;
using Quaver.Shared.Graphics.Dialogs;
using Quaver.Shared.Helpers;
using Quaver.Shared.Online.Workshop;
using Wobble.Assets;
using Wobble.Graphics;
using Wobble.Graphics.Sprites;
using Wobble.Graphics.Sprites.Text;
using Wobble.Graphics.UI.Buttons;
using Wobble.Graphics.UI.Dialogs;
using Wobble.Graphics.UI.Form;
using Wobble.Input;
using Wobble.Managers;
using Wobble.Platform;

namespace Quaver.Shared.Screens.Workshop
{
    public sealed class SteamAuthDialog : DialogScreen
    {
        private readonly Action _onAuthenticated;
        private CancellationTokenSource _cts;

        private Sprite _panel;
        private ImageButton _tabCredsBtn;
        private ImageButton _tabQrBtn;
        private Container _credsContainer;
        private Container _qrContainer;

        private Textbox _userBox;
        private Textbox _passBox;
        private string _usernameValue = string.Empty;
        private string _passwordValue = string.Empty;
        private bool _rememberSession = true;

        private ImageButton _rememberBtn;
        private SpriteTextPlus _rememberLabel;
        private ImageButton _loginBtn;
        private SpriteTextPlus _loginBtnLabel;
        private SpriteTextPlus _statusText;

        private SpriteTextPlus _qrUrlText;
        private string _currentChallengeUrl = string.Empty;
        private ImageButton _openSteamAppBtn;
        private ImageButton _copyUrlBtn;
        private ImageButton _refreshQrBtn;

        private TaskCompletionSource<string> _guardTcs;

        public SteamAuthDialog(Action onAuthenticated = null) : base(0.78f)
        {
            _onAuthenticated = onAuthenticated;
            _cts = new CancellationTokenSource();
            CreateContent();
        }

        public override void CreateContent()
        {
            _panel = new Sprite
            {
                Parent = Container,
                Alignment = Alignment.MidCenter,
                Size = new ScalableVector2(860, 620),
                Tint = ColorHelper.HexToColor("#1C1F2B")
            };
            _panel.AddBorder(ColorHelper.HexToColor("#3B82F6"), 2);

            new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterBold), "INICIAR SESIÓN EN STEAM", 26)
            {
                Parent = _panel,
                Alignment = Alignment.TopLeft,
                Position = new ScalableVector2(30, 24),
                Tint = Color.White
            };

            var closeBtn = CreateStyledButton(_panel, "CERRAR", new ScalableVector2(120, 42),
                ColorHelper.HexToColor("#3A2429"), ColorHelper.HexToColor("#EF4444"),
                (o, e) => CloseDialog());
            closeBtn.Alignment = Alignment.TopRight;
            closeBtn.Position = new ScalableVector2(-24, 20);

            _tabCredsBtn = CreateStyledButton(_panel, "USUARIO Y CONTRASEÑA", new ScalableVector2(385, 48),
                ColorHelper.HexToColor("#2563EB"), ColorHelper.HexToColor("#60A5FA"),
                (o, e) => SwitchMode(false));
            _tabCredsBtn.Position = new ScalableVector2(30, 82);

            _tabQrBtn = CreateStyledButton(_panel, "STEAM MOBILE APP / QR", new ScalableVector2(385, 48),
                ColorHelper.HexToColor("#272B3B"), ColorHelper.HexToColor("#4B5563"),
                (o, e) => SwitchMode(true));
            _tabQrBtn.Position = new ScalableVector2(445, 82);

            CreateCredentialsTab();
            CreateQrTab();

            _statusText = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterRegular),
                "Autenticación directa mediante SteamKit2 (cifrada E2E, tu token se guarda localmente).", 18)
            {
                Parent = _panel,
                Position = new ScalableVector2(30, 488),
                MaxWidth = 800,
                Tint = ColorHelper.HexToColor("#93C5FD")
            };

            var anonBtn = CreateStyledButton(_panel, "CONTINUAR EN MODO ANÓNIMO", new ScalableVector2(380, 46),
                ColorHelper.HexToColor("#2A2E3D"), ColorHelper.HexToColor("#64748B"),
                (o, e) => StartAnonymous());
            anonBtn.Alignment = Alignment.BotLeft;
            anonBtn.Position = new ScalableVector2(30, -24);

            SwitchMode(false);
        }

        private void CreateCredentialsTab()
        {
            _credsContainer = new Container
            {
                Parent = _panel,
                Position = new ScalableVector2(30, 150),
                Size = new ScalableVector2(800, 320)
            };

            new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "Usuario de Steam:", 20)
            {
                Parent = _credsContainer,
                Position = new ScalableVector2(0, 4),
                Tint = Color.White
            };

            _userBox = new Textbox(new ScalableVector2(800, 56), FontManager.GetWobbleFont(Fonts.InterSemiBold),
                22, "", "Toca para introducir tu usuario de Steam")
            {
                Parent = _credsContainer,
                Position = new ScalableVector2(0, 36),
                Tint = ColorHelper.HexToColor("#11131C"),
                AllowSubmission = false
            };
            _userBox.AddBorder(ColorHelper.HexToColor("#3F4865"), 2);
            _userBox.Button.Clicked += (o, e) => PromptField("Usuario de Steam", _usernameValue, false, val =>
            {
                _usernameValue = val;
                _userBox.RawText = val;
            });

            new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "Contraseña:", 20)
            {
                Parent = _credsContainer,
                Position = new ScalableVector2(0, 110),
                Tint = Color.White
            };

            _passBox = new Textbox(new ScalableVector2(800, 56), FontManager.GetWobbleFont(Fonts.InterSemiBold),
                22, "", "Toca para introducir tu contraseña")
            {
                Parent = _credsContainer,
                Position = new ScalableVector2(0, 142),
                Tint = ColorHelper.HexToColor("#11131C"),
                AllowSubmission = false
            };
            _passBox.AddBorder(ColorHelper.HexToColor("#3F4865"), 2);
            _passBox.Button.Clicked += (o, e) => PromptField("Contraseña de Steam", _passwordValue, true, val =>
            {
                _passwordValue = val;
                _passBox.RawText = string.IsNullOrEmpty(val) ? string.Empty : new string('*', Math.Min(val.Length, 24));
            });

            _rememberBtn = CreateStyledButton(_credsContainer, "[X] Recordar sesión (RefreshToken)", new ScalableVector2(410, 48),
                ColorHelper.HexToColor("#232838"), ColorHelper.HexToColor("#475569"),
                (o, e) =>
                {
                    _rememberSession = !_rememberSession;
                    _rememberLabel.Text = (_rememberSession ? "[X] " : "[ ] ") + "Recordar sesión (RefreshToken)";
                });
            _rememberBtn.Position = new ScalableVector2(0, 224);
            _rememberLabel = FindLabel(_rememberBtn);

            _loginBtn = CreateStyledButton(_credsContainer, "INICIAR SESIÓN", new ScalableVector2(360, 56),
                ColorHelper.HexToColor("#16A34A"), ColorHelper.HexToColor("#4ADE80"),
                (o, e) => StartCredentialsLogin());
            _loginBtn.Position = new ScalableVector2(440, 220);
            _loginBtnLabel = FindLabel(_loginBtn);
        }

        private void CreateQrTab()
        {
            _qrContainer = new Container
            {
                Parent = _panel,
                Position = new ScalableVector2(30, 150),
                Size = new ScalableVector2(800, 320),
                Visible = false
            };

            new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold),
                "Aprueba el inicio de sesión directamente en la app oficial de Steam en este teléfono:", 20)
            {
                Parent = _qrContainer,
                Position = new ScalableVector2(0, 10),
                MaxWidth = 800,
                Tint = Color.White
            };

            var urlBox = new Sprite
            {
                Parent = _qrContainer,
                Position = new ScalableVector2(0, 74),
                Size = new ScalableVector2(800, 80),
                Tint = ColorHelper.HexToColor("#11131C")
            };
            urlBox.AddBorder(ColorHelper.HexToColor("#3B82F6"), 2);

            _qrUrlText = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterRegular), "Generando enlace Steam Auth...", 18)
            {
                Parent = urlBox,
                Alignment = Alignment.MidLeft,
                Position = new ScalableVector2(16, 0),
                MaxWidth = 768,
                Tint = ColorHelper.HexToColor("#93C5FD")
            };

            _openSteamAppBtn = CreateStyledButton(_qrContainer, "ABRIR EN STEAM APP", new ScalableVector2(390, 58),
                ColorHelper.HexToColor("#2563EB"), ColorHelper.HexToColor("#60A5FA"),
                (o, e) =>
                {
                    if (!string.IsNullOrEmpty(_currentChallengeUrl))
                        BrowserHelper.OpenURL(_currentChallengeUrl, true);
                });
            _openSteamAppBtn.Position = new ScalableVector2(0, 178);

            _copyUrlBtn = CreateStyledButton(_qrContainer, "COPIAR ENLACE", new ScalableVector2(190, 58),
                ColorHelper.HexToColor("#2D3348"), ColorHelper.HexToColor("#64748B"),
                (o, e) =>
                {
                    if (!string.IsNullOrEmpty(_currentChallengeUrl))
                        AndroidPlatformBridge.CopyTextHandler?.Invoke(_currentChallengeUrl);
                });
            _copyUrlBtn.Position = new ScalableVector2(410, 178);

            _refreshQrBtn = CreateStyledButton(_qrContainer, "RENOVAR", new ScalableVector2(180, 58),
                ColorHelper.HexToColor("#2D3348"), ColorHelper.HexToColor("#64748B"),
                (o, e) => StartQrLogin());
            _refreshQrBtn.Position = new ScalableVector2(620, 178);
        }

        private void SwitchMode(bool qr)
        {
            _credsContainer.Visible = !qr;
            _qrContainer.Visible = qr;
            _tabCredsBtn.Tint = qr ? ColorHelper.HexToColor("#272B3B") : ColorHelper.HexToColor("#2563EB");
            _tabQrBtn.Tint = qr ? ColorHelper.HexToColor("#2563EB") : ColorHelper.HexToColor("#272B3B");

            if (qr && string.IsNullOrEmpty(_currentChallengeUrl))
                StartQrLogin();
        }

        private void PromptField(string title, string initial, bool isPassword, Action<string> onUpdated)
        {
            if (OperatingSystem.IsAndroid() && AndroidPlatformBridge.PromptTextHandler != null)
            {
                AndroidPlatformBridge.PromptTextHandler(title, initial, isPassword, val =>
                {
                    AddScheduledUpdate(() => onUpdated?.Invoke(val ?? string.Empty));
                });
            }
        }

        private void StartCredentialsLogin()
        {
            var user = string.IsNullOrWhiteSpace(_usernameValue) ? _userBox.RawText : _usernameValue;
            var pass = string.IsNullOrEmpty(_passwordValue) ? _passBox.RawText : _passwordValue;
            if (string.IsNullOrWhiteSpace(user) || string.IsNullOrEmpty(pass))
            {
                SetStatus("Introduce usuario y contraseña de Steam.", ColorHelper.HexToColor("#FBBF24"));
                return;
            }

            ResetCts();
            var ct = _cts.Token;
            SetStatus("Conectando con Steam...", ColorHelper.HexToColor("#93C5FD"));
            _loginBtn.IsClickable = false;

            var authenticator = new InteractiveSteamAuthenticator(
                prevWrong => RequestGuardCodeAsync(prevWrong ? "Código Steam Guard incorrecto. Inténtalo de nuevo:" : "Introduce tu código de Steam Guard (App móvil):"),
                (email, prevWrong) => RequestGuardCodeAsync(prevWrong ? $"Código de email incorrecto ({email}):" : $"Código enviado al email {email}:"),
                () =>
                {
                    AddScheduledUpdate(() => SetStatus("Confirma el inicio de sesión en tu Steam Mobile App...", ColorHelper.HexToColor("#FBBF24")));
                    return Task.FromResult(true);
                });

            Task.Run(async () =>
            {
                var (ok, msg) = await SteamWorkshopService.Instance
                    .SignInWithCredentialsAsync(user, pass, _rememberSession, authenticator, ct)
                    .ConfigureAwait(false);

                AddScheduledUpdate(() =>
                {
                    _loginBtn.IsClickable = true;
                    SetStatus(msg, ok ? ColorHelper.HexToColor("#4ADE80") : ColorHelper.HexToColor("#F87171"));
                    if (ok)
                    {
                        _onAuthenticated?.Invoke();
                        CloseDialog();
                    }
                });
            }, ct);
        }

        private Task<string> RequestGuardCodeAsync(string promptTitle)
        {
            var tcs = new TaskCompletionSource<string>(TaskCreationOptions.RunContinuationsAsynchronously);
            _guardTcs = tcs;

            AddScheduledUpdate(() =>
            {
                SetStatus(promptTitle, ColorHelper.HexToColor("#FBBF24"));
                if (OperatingSystem.IsAndroid() && AndroidPlatformBridge.PromptTextHandler != null)
                {
                    AndroidPlatformBridge.PromptTextHandler(promptTitle, string.Empty, false, code =>
                    {
                        tcs.TrySetResult(code?.Trim() ?? string.Empty);
                    });
                }
                else
                {
                    var dialog = new YesNoTextDialog("STEAM GUARD", promptTitle, "", "Código 2FA",
                        code => tcs.TrySetResult(code?.Trim() ?? string.Empty),
                        () => tcs.TrySetResult(string.Empty));
                    DialogManager.Show(dialog);
                }
            });

            return tcs.Task;
        }

        private void StartQrLogin()
        {
            ResetCts();
            var ct = _cts.Token;
            _currentChallengeUrl = string.Empty;
            _qrUrlText.Text = "Generando enlace de sesión Steam...";
            SetStatus("Esperando aprobación en Steam Mobile App...", ColorHelper.HexToColor("#93C5FD"));

            Task.Run(async () =>
            {
                var (ok, msg) = await SteamWorkshopService.Instance.StartQrSignInAsync(true, url =>
                {
                    AddScheduledUpdate(() =>
                    {
                        _currentChallengeUrl = url ?? string.Empty;
                        _qrUrlText.Text = _currentChallengeUrl;
                    });
                }, ct).ConfigureAwait(false);

                AddScheduledUpdate(() =>
                {
                    SetStatus(msg, ok ? ColorHelper.HexToColor("#4ADE80") : ColorHelper.HexToColor("#F87171"));
                    if (ok)
                    {
                        _onAuthenticated?.Invoke();
                        CloseDialog();
                    }
                });
            }, ct);
        }

        private void StartAnonymous()
        {
            ResetCts();
            var ct = _cts.Token;
            SetStatus("Conectando en modo anónimo...", ColorHelper.HexToColor("#93C5FD"));
            Task.Run(async () =>
            {
                var ok = await SteamWorkshopService.Instance.SwitchToAnonymousAsync(ct).ConfigureAwait(false);
                AddScheduledUpdate(() =>
                {
                    if (ok)
                    {
                        _onAuthenticated?.Invoke();
                        CloseDialog();
                    }
                    else
                    {
                        SetStatus(SteamWorkshopService.Instance.LastAuthMessage, ColorHelper.HexToColor("#F87171"));
                    }
                });
            }, ct);
        }

        private void SetStatus(string text, Color color)
        {
            _statusText.Text = text ?? string.Empty;
            _statusText.Tint = color;
        }

        private void ResetCts()
        {
            try { _cts?.Cancel(); } catch { }
            try { _cts?.Dispose(); } catch { }
            _cts = new CancellationTokenSource();
        }

        public void CloseDialog()
        {
            ResetCts();
            _guardTcs?.TrySetResult(string.Empty);
            DialogManager.Dismiss(this);
        }

        public override void Update(GameTime gameTime)
        {
            if (!OperatingSystem.IsAndroid())
            {
                if (_userBox.Focused)
                    _usernameValue = _userBox.RawText;
            }
            base.Update(gameTime);
        }

        public override void HandleInput(GameTime gameTime)
        {
            if (IsOnTop && KeyboardManager.IsUniqueKeyPress(Keys.Escape))
                CloseDialog();
        }

        public override void Destroy()
        {
            ResetCts();
            _guardTcs?.TrySetResult(string.Empty);
            base.Destroy();
        }

        private static ImageButton CreateStyledButton(Drawable parent, string label, ScalableVector2 size, Color fill, Color border, EventHandler onClick)
        {
            var btn = new ImageButton(WobbleAssets.WhiteBox, onClick)
            {
                Parent = parent,
                Size = size,
                Tint = fill
            };
            btn.AddBorder(border, 2);
            new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), label, 18)
            {
                Parent = btn,
                Alignment = Alignment.MidCenter,
                Tint = Color.White
            };
            return btn;
        }

        private static SpriteTextPlus FindLabel(Drawable btn)
        {
            foreach (var c in btn.Children)
            {
                if (c is SpriteTextPlus st)
                    return st;
            }
            return null;
        }
    }
}
""",
    encoding="utf-8",
)
(wui_dir / "SteamWorkshopScreen.cs").write_text(
    r"""#nullable disable
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Quaver.Server.Client.Enums;
using Quaver.Server.Client.Objects;
using Quaver.Shared.Config;
using Quaver.Shared.Database.Maps;
using Quaver.Shared.Modifiers;
using Quaver.Shared.Online.Workshop;
using Wobble.Input;
using Wobble.Screens;

namespace Quaver.Shared.Screens.Workshop
{
    public sealed class SteamWorkshopScreen : QuaverScreen
    {
        public override QuaverScreenType Type => QuaverScreenType.Workshop;

        public override ScreenView View { get; protected set; }

        public SteamWorkshopScreen()
        {
            View = new SteamWorkshopScreenView(this);
        }

        public override void OnFirstUpdate()
        {
            base.OnFirstUpdate();
            (View as SteamWorkshopScreenView)?.InitializeLoad();
        }

        public override void Update(GameTime gameTime)
        {
            base.Update(gameTime);

            if (!Exiting && KeyboardManager.IsUniqueKeyPress(Keys.Escape))
                ExitToMenu();
        }

        public void ExitToMenu()
        {
            if (Exiting)
                return;

            Exit(() =>
            {
                if (MapsetImporter.Queue.Count > 0)
                    return QuaverScreenFactory.CreateImporting();
                return QuaverScreenFactory.CreateMainMenu();
            });
        }

        public void ExitToImporting()
        {
            if (Exiting)
                return;
            Exit(() => QuaverScreenFactory.CreateImporting());
        }

        public override UserClientStatus GetClientStatus()
            => new UserClientStatus(ClientStatus.InMenus, -1, "", (byte)ConfigManager.SelectedGameMode.Value, "", (long)ModManager.Mods);
    }
}
""",
    encoding="utf-8",
) 


(wui_dir / "SteamWorkshopScreenView.cs").write_text(
    r"""#nullable disable
using System;
using System.Collections.Generic;
using System.IO;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Graphics;
using Microsoft.Xna.Framework.Input;
using MonoGame.Extended;
using Quaver.Shared.Assets;
using Quaver.Shared.Database.Maps;
using Quaver.Shared.Graphics;
using Quaver.Shared.Graphics.Backgrounds;
using Quaver.Shared.Graphics.Dialogs;
using Quaver.Shared.Graphics.Menu.Border;
using Quaver.Shared.Graphics.Menu.Border.Components;
using Quaver.Shared.Graphics.Notifications;
using Quaver.Shared.Helpers;
using Quaver.Shared.Online.Workshop;
using Wobble;
using Wobble.Assets;
using Wobble.Graphics;
using Wobble.Graphics.Animations;
using Wobble.Graphics.Sprites;
using Wobble.Graphics.Sprites.Text;
using Wobble.Graphics.UI;
using Wobble.Graphics.UI.Buttons;
using Wobble.Graphics.UI.Dialogs;
using Wobble.Input;
using Wobble.Managers;
using Wobble.Platform;
using Wobble.Screens;
using Wobble.Window;
using ColorHelper = Quaver.Shared.Helpers.ColorHelper; 
namespace Quaver.Shared.Screens.Workshop
{
    internal sealed class WorkshopTouchScrollContainer : ScrollContainer
    {
        private bool _pointerDown;
        private float _startY;
        private float _lastY;
        public bool WasDraggingRecently { get; private set; }

        public WorkshopTouchScrollContainer(ScalableVector2 size, ScalableVector2 contentSize)
            : base(size, contentSize)
        {
            InputEnabled = true;
            AllowScrollbarDragging = true;
            Scrollbar.Tint = ColorHelper.HexToColor("#60A5FA");
            Scrollbar.Width = 6;
            EasingType = Easing.OutQuint;
            TimeToCompleteScroll = 350;
            ScrollSpeed = 90;
        } 

        public override void Update(GameTime gameTime)
        {
            var leftPressed = MouseManager.CurrentState.LeftButton == ButtonState.Pressed;
            var pos = MouseManager.CurrentState.Position;

            if (InputEnabled && MouseManager.IsUniquePress(MouseButton.Left) && IsHovered() && !Scrollbar.IsHovered())
            {
                _pointerDown = true;
                _startY = pos.Y;
                _lastY = pos.Y;
                WasDraggingRecently = false;
            }
            else if (_pointerDown && leftPressed)
            {
                var dy = pos.Y - _lastY;
                _lastY = pos.Y;
                if (Math.Abs(pos.Y - _startY) > 12f)
                {
                    WasDraggingRecently = true;
                    TargetY += dy;
                }
            }
            else if (!leftPressed)
            {
                _pointerDown = false;
            }

            base.Update(gameTime);
        }
    }

    internal sealed class WorkshopClippedButton : ImageButton
    {
        private readonly Drawable _clipParent;

        public WorkshopClippedButton(Drawable clipParent, WorkshopTouchScrollContainer scroll, Texture2D image, EventHandler onClick)
            : base(image, (s, e) =>
            {
                if (scroll != null && scroll.WasDraggingRecently)
                    return;
                onClick?.Invoke(s, e);
            })
        {
            _clipParent = clipParent;
        }

        protected override bool IsMouseInClickArea()
        {
            if (_clipParent == null)
                return base.IsMouseInClickArea();
            var rect = RectangleF.Intersection(ScreenRectangle, _clipParent.ScreenRectangle);
            return !rect.IsEmpty && GraphicsHelper.RectangleContains(rect, MouseManager.CurrentState.Position);
        }
    }

    public sealed class SteamWorkshopScreenView : ScreenView
    {
        private readonly SteamWorkshopScreen _workshopScreen;
        private readonly Dictionary<string, Texture2D> _thumbCache = new Dictionary<string, Texture2D>();
        private readonly List<WorkshopClippedButton> _cards = new List<WorkshopClippedButton>();
        private readonly List<(WorkshopBrowseMode mode, ImageButton btn)> _modeButtons = new List<(WorkshopBrowseMode, ImageButton)>();

        private WorkshopBrowseMode _mode = WorkshopBrowseMode.All;
        private WorkshopSortMode _sort = WorkshopSortMode.Trending;
        private string _searchQuery = string.Empty;
        private int _page = 1;
        private uint _total;
        private bool _hasMore;

        private WorkshopItemInfo _selectedItem;
        private CancellationTokenSource _queryCts;
        private CancellationTokenSource _downloadCts;
        private bool _isDownloading;

        private Sprite _authBadgeBg;
        private SpriteTextPlus _authStatusLabel;
        private ImageButton _authActionBtn;
        private SpriteTextPlus _authActionBtnLabel;
        private ImageButton _searchBtn;
        private SpriteTextPlus _searchLabel;
        private ImageButton _sortBtn;
        private SpriteTextPlus _sortLabel;
        private SpriteTextPlus _pageLabel;

        private WorkshopTouchScrollContainer _scrollContainer;
        private LoadingWheel _loadingWheel;
        private SpriteTextPlus _emptyNoticeText;

        private Sprite _detailThumb;
        private SpriteTextPlus _detailTitle;
        private SpriteTextPlus _detailMeta;
        private SpriteTextPlus _detailDesc;
        private SpriteTextPlus _detailDestInfo;
        private Sprite _progressBg;
        private Sprite _progressFill;
        private SpriteTextPlus _progressLabel;

        private ImageButton _downloadBtn;
        private SpriteTextPlus _downloadBtnLabel;
        private ImageButton _applySkinBtn;
        private ImageButton _subscribeBtn;
        private ImageButton _openWebBtn;
        private ImageButton _deleteLocalBtn;
        private ImageButton _importMapsBtn;

        public SteamWorkshopScreenView(SteamWorkshopScreen screen) : base(screen)
        {
            _workshopScreen = screen;
            BuildLayout();
            SteamWorkshopService.Instance.AuthStateChanged += OnServiceAuthChanged;
        }

        private void BuildLayout()
        {
            var w = WindowManager.Width;
            var h = WindowManager.Height;
            var padX = 36f;

            new BackgroundImage(UserInterface.TrianglesWallpaper, 0, false) { Parent = Container };
            new MenuHeaderMain { Parent = Container };

            var topBarY = MenuBorder.HEIGHT + 16f;
            _authBadgeBg = new Sprite
            {
                Parent = Container,
                Position = new ScalableVector2(padX, topBarY),
                Size = new ScalableVector2(w - padX * 2f, 62f),
                Tint = ColorHelper.HexToColor("#161925")
            };
            _authBadgeBg.AddBorder(ColorHelper.HexToColor("#2E3650"), 2);

            _authStatusLabel = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "Steam: Conectando...", 19)
            {
                Parent = _authBadgeBg,
                Alignment = Alignment.MidLeft,
                Position = new ScalableVector2(18, 0),
                Tint = Color.White
            };

            _authActionBtn = MakeButton(_authBadgeBg, "CUENTA STEAM", new ScalableVector2(210, 44),
                ColorHelper.HexToColor("#2563EB"), ColorHelper.HexToColor("#60A5FA"),
                (o, e) => DialogManager.Show(new SteamAuthDialog(() => RefreshCurrentQuery())));
            _authActionBtn.Alignment = Alignment.MidLeft;
            _authActionBtn.Position = new ScalableVector2(420, 0);
            _authActionBtnLabel = GetButtonText(_authActionBtn);

            _searchBtn = MakeButton(_authBadgeBg, "Buscar mapa, skin, plugin o pegar ID / URL...",
                new ScalableVector2(Math.Max(260, _authBadgeBg.Width - 820), 44),
                ColorHelper.HexToColor("#0F121B"), ColorHelper.HexToColor("#475569"),
                (o, e) => OpenSearchPrompt());
            _searchBtn.Alignment = Alignment.MidRight;
            _searchBtn.Position = new ScalableVector2(-150, 0);
            _searchLabel = GetButtonText(_searchBtn);

            var goSearchBtn = MakeButton(_authBadgeBg, "BUSCAR", new ScalableVector2(124, 44),
                ColorHelper.HexToColor("#0EA5E9"), ColorHelper.HexToColor("#7DD3FC"),
                (o, e) =>
                {
                    _page = 1;
                    RefreshCurrentQuery();
                });
            goSearchBtn.Alignment = Alignment.MidRight;
            goSearchBtn.Position = new ScalableVector2(-14, 0);

            var filterY = topBarY + 74f;
            var categories = new (WorkshopBrowseMode mode, string title, float width)[]
            {
                (WorkshopBrowseMode.All, "Todos", 104),
                (WorkshopBrowseMode.Skins, "Skins", 104),
                (WorkshopBrowseMode.Plugins, "Plugins", 116),
                (WorkshopBrowseMode.Collections, "Colecciones", 148),
                (WorkshopBrowseMode.MySubscriptions, "Suscripciones", 164),
                (WorkshopBrowseMode.Installed, "Instalados", 136),
            };

            var cx = padX;
            foreach (var c in categories)
            {
                var cat = c;
                var b = MakeButton(Container, cat.title, new ScalableVector2(cat.width, 42),
                    ColorHelper.HexToColor("#1E2434"), ColorHelper.HexToColor("#3B82F6"),
                    (o, e) =>
                    {
                        _mode = cat.mode;
                        _page = 1;
                        UpdateFilterHighlights();
                        RefreshCurrentQuery();
                    });
                b.Position = new ScalableVector2(cx, filterY);
                _modeButtons.Add((cat.mode, b));
                cx += cat.width + 10f;
            }

            _sortBtn = MakeButton(Container, "Orden: Tendencias", new ScalableVector2(230, 42),
                ColorHelper.HexToColor("#1E2434"), ColorHelper.HexToColor("#64748B"),
                (o, e) => CycleSort());
            _sortBtn.Alignment = Alignment.TopRight;
            _sortBtn.Position = new ScalableVector2(-padX - 230f, filterY);
            _sortLabel = GetButtonText(_sortBtn);

            var prevBtn = MakeButton(Container, "<", new ScalableVector2(50, 42),
                ColorHelper.HexToColor("#1E2434"), ColorHelper.HexToColor("#64748B"),
                (o, e) =>
                {
                    if (_page > 1)
                    {
                        _page--;
                        RefreshCurrentQuery();
                    }
                });
            prevBtn.Alignment = Alignment.TopRight;
            prevBtn.Position = new ScalableVector2(-padX - 166f, filterY);

            _pageLabel = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "Pág 1", 18)
            {
                Parent = Container,
                Alignment = Alignment.TopRight,
                Position = new ScalableVector2(-padX - 88f, filterY + 10f),
                Tint = Color.White
            };

            var nextBtn = MakeButton(Container, ">", new ScalableVector2(50, 42),
                ColorHelper.HexToColor("#1E2434"), ColorHelper.HexToColor("#64748B"),
                (o, e) =>
                {
                    if (_hasMore)
                    {
                        _page++;
                        RefreshCurrentQuery();
                    }
                });
            nextBtn.Alignment = Alignment.TopRight;
            nextBtn.Position = new ScalableVector2(-padX, filterY);

            var bodyY = filterY + 56f;
            var bodyH = h - bodyY - MenuBorder.HEIGHT - 16f;
            var detailW = Math.Clamp(w * 0.36f, 460f, 580f);
            var listW = w - padX * 2f - detailW - 24f;

            var listPanel = new Sprite
            {
                Parent = Container,
                Position = new ScalableVector2(padX, bodyY),
                Size = new ScalableVector2(listW, bodyH),
                Tint = ColorHelper.HexToColor("#121520")
            };
            listPanel.AddBorder(ColorHelper.HexToColor("#2A3147"), 2);

            _scrollContainer = new WorkshopTouchScrollContainer(
                new ScalableVector2(listW - 12f, bodyH - 12f),
                new ScalableVector2(listW - 12f, bodyH - 12f))
            {
                Parent = listPanel,
                Position = new ScalableVector2(6, 6),
                Tint = Color.Transparent
            };

            _loadingWheel = new LoadingWheel
            {
                Parent = listPanel,
                Alignment = Alignment.MidCenter,
                Size = new ScalableVector2(64, 64),
                Visible = false
            };

            _emptyNoticeText = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "", 20)
            {
                Parent = listPanel,
                Alignment = Alignment.MidCenter,
                TextAlignment = TextAlignment.Center,
                MaxWidth = listW - 80f,
                Tint = ColorHelper.HexToColor("#CBD5E1"),
                Visible = false
            };

            var detailPanel = new Sprite
            {
                Parent = Container,
                Alignment = Alignment.TopRight,
                Position = new ScalableVector2(-padX, bodyY),
                Size = new ScalableVector2(detailW, bodyH),
                Tint = ColorHelper.HexToColor("#161925")
            };
            detailPanel.AddBorder(ColorHelper.HexToColor("#2A3147"), 2);

            var previewW = detailW - 36f;
            var previewH = Math.Min(230f, previewW * 0.52f);
            _detailThumb = new Sprite
            {
                Parent = detailPanel,
                Alignment = Alignment.TopCenter,
                Position = new ScalableVector2(0, 18),
                Size = new ScalableVector2(previewW, previewH),
                Image = UserInterface.DefaultBanner
            };
            _detailThumb.AddBorder(ColorHelper.HexToColor("#334155"), 2);

            var textY = previewH + 30f;
            _detailTitle = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterBold), "Selecciona un elemento de Workshop", 22)
            {
                Parent = detailPanel,
                Position = new ScalableVector2(18, textY),
                MaxWidth = previewW,
                Tint = Color.White
            };

            _detailMeta = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterMedium), "", 16)
            {
                Parent = detailPanel,
                Position = new ScalableVector2(18, textY + 52f),
                MaxWidth = previewW,
                Tint = ColorHelper.HexToColor("#93C5FD")
            };

            _detailDesc = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterRegular), "", 16)
            {
                Parent = detailPanel,
                Position = new ScalableVector2(18, textY + 96f),
                MaxWidth = previewW,
                Tint = ColorHelper.HexToColor("#CBD5E1")
            };

            _detailDestInfo = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterRegular),
                "Destino Android: Workshop/ y Songs/", 15)
            {
                Parent = detailPanel,
                Position = new ScalableVector2(18, bodyH - 224f),
                MaxWidth = previewW,
                Tint = ColorHelper.HexToColor("#94A3B8")
            };

            _progressBg = new Sprite
            {
                Parent = detailPanel,
                Position = new ScalableVector2(18, bodyH - 194f),
                Size = new ScalableVector2(previewW, 24f),
                Tint = ColorHelper.HexToColor("#0F172A")
            };
            _progressBg.AddBorder(ColorHelper.HexToColor("#334155"), 1);

            _progressFill = new Sprite
            {
                Parent = _progressBg,
                Position = new ScalableVector2(0, 0), 
                Size = new ScalableVector2(0, 24f),
                Tint = ColorHelper.HexToColor("#22C55E")
            };

            _progressLabel = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "Listo para descargar", 15)
            {
                Parent = _progressBg,
                Alignment = Alignment.MidCenter,
                Tint = Color.White
            };

            _downloadBtn = MakeButton(detailPanel, "DESCARGAR E INSTALAR", new ScalableVector2(previewW, 50),
                ColorHelper.HexToColor("#16A34A"), ColorHelper.HexToColor("#4ADE80"),
                (o, e) => StartDownloadOrCancel());
            _downloadBtn.Position = new ScalableVector2(18, bodyH - 158f);
            _downloadBtnLabel = GetButtonText(_downloadBtn);

            var halfW = (previewW - 10f) / 2f;
            _applySkinBtn = MakeButton(detailPanel, "APLICAR SKIN", new ScalableVector2(halfW, 42),
                ColorHelper.HexToColor("#2563EB"), ColorHelper.HexToColor("#60A5FA"),
                (o, e) => ApplySelectedSkin());
            _applySkinBtn.Position = new ScalableVector2(18, bodyH - 100f);

            _subscribeBtn = MakeButton(detailPanel, "SUSCRIBIRSE", new ScalableVector2(halfW, 42),
                ColorHelper.HexToColor("#334155"), ColorHelper.HexToColor("#64748B"),
                (o, e) => ToggleSubscribe());
            _subscribeBtn.Position = new ScalableVector2(18 + halfW + 10f, bodyH - 100f);

            _openWebBtn = MakeButton(detailPanel, "VER EN STEAM WEB", new ScalableVector2(halfW, 40),
                ColorHelper.HexToColor("#1E293B"), ColorHelper.HexToColor("#475569"),
                (o, e) =>
                {
                    if (_selectedItem != null)
                        BrowserHelper.OpenURL($"https://steamcommunity.com/sharedfiles/filedetails/?id={_selectedItem.PublishedFileId}", true);
                });
            _openWebBtn.Position = new ScalableVector2(18, bodyH - 52f);

            _deleteLocalBtn = MakeButton(detailPanel, "ELIMINAR LOCAL", new ScalableVector2(halfW, 40),
                ColorHelper.HexToColor("#451A22"), ColorHelper.HexToColor("#EF4444"),
                (o, e) => DeleteSelectedLocal());
            _deleteLocalBtn.Position = new ScalableVector2(18 + halfW + 10f, bodyH - 52f);

            _importMapsBtn = new ImageButton(WobbleAssets.WhiteBox, (o, e) => _workshopScreen.ExitToImporting())
            {
                Size = new ScalableVector2(240, 36),
                Tint = ColorHelper.HexToColor("#15803D"),
                Visible = false
            };
            _importMapsBtn.AddBorder(ColorHelper.HexToColor("#4ADE80"), 1);
            new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "IMPORTAR MAPAS EN COLA", 16)
            {
                Parent = _importMapsBtn,
                Alignment = Alignment.MidCenter,
                Tint = Color.White
            };

            var backBtn = new IconTextButton(FontAwesome.Get(FontAwesomeIcon.fa_chevron_pointing_to_the_left),
                FontManager.GetWobbleFont(Fonts.InterSemiBold), "Volver",
                (o, e) => _workshopScreen.ExitToMenu());

            var logoutBtn = new IconTextButton(FontAwesome.Get(FontAwesomeIcon.fa_settings),
                FontManager.GetWobbleFont(Fonts.InterSemiBold), "Cuenta / Cerrar Sesión Steam",
                (o, e) =>
                {
                    if (SteamWorkshopService.Instance.IsAuthenticated)
                        SteamWorkshopService.Instance.SignOut();
                    DialogManager.Show(new SteamAuthDialog(() => RefreshCurrentQuery()));
                });

            new MenuBorder(MenuBorderType.Footer,
                new List<Drawable> { backBtn, logoutBtn },
                new List<Drawable> { _importMapsBtn })
            {
                Parent = Container,
                Alignment = Alignment.BotLeft
            };

            UpdateFilterHighlights();
            UpdateAuthBanner();
            UpdateDetailPanel(null);
        }

        public void InitializeLoad()
        {
            RefreshCurrentQuery();
        }

        private void OnServiceAuthChanged()
        {
            Container.AddScheduledUpdate(UpdateAuthBanner);
        }

        private void UpdateAuthBanner()
        {
            var svc = SteamWorkshopService.Instance;
            if (svc.IsAuthenticated)
            {
                _authStatusLabel.Text = $"Steam: {svc.AccountName} (Autenticado)";
                _authStatusLabel.Tint = ColorHelper.HexToColor("#4ADE80");
                if (_authActionBtnLabel != null)
                    _authActionBtnLabel.Text = "CAMBIAR CUENTA";
            }
            else if (svc.AuthState == WorkshopAuthState.Anonymous)
            {
                _authStatusLabel.Text = "Steam: Modo Anónimo (público)";
                _authStatusLabel.Tint = ColorHelper.HexToColor("#FBBF24");
                if (_authActionBtnLabel != null)
                    _authActionBtnLabel.Text = "INICIAR SESIÓN";
            }
            else
            {
                _authStatusLabel.Text = string.IsNullOrEmpty(svc.LastAuthMessage)
                    ? "Steam: Desconectado"
                    : $"Steam: {svc.LastAuthMessage}";
                _authStatusLabel.Tint = ColorHelper.HexToColor("#93C5FD");
                if (_authActionBtnLabel != null)
                    _authActionBtnLabel.Text = "INICIAR SESIÓN";
            }
            _importMapsBtn.Visible = MapsetImporter.Queue.Count > 0;
        }

        private void UpdateFilterHighlights()
        {
            foreach (var (mode, btn) in _modeButtons)
                btn.Tint = mode == _mode ? ColorHelper.HexToColor("#2563EB") : ColorHelper.HexToColor("#1E2434");
        }

        private void CycleSort()
        {
            _sort = (WorkshopSortMode)(((int)_sort + 1) % 5);
            _sortLabel.Text = _sort switch
            {
                WorkshopSortMode.Trending => "Orden: Tendencias",
                WorkshopSortMode.MostSubscribed => "Orden: Suscritos",
                WorkshopSortMode.TopRated => "Orden: Valorados",
                WorkshopSortMode.Newest => "Orden: Recientes",
                WorkshopSortMode.RecentlyUpdated => "Orden: Actualizados",
                _ => "Orden: Tendencias"
            };
            _page = 1;
            RefreshCurrentQuery();
        }

        private void OpenSearchPrompt()
        {
            if (OperatingSystem.IsAndroid() && AndroidPlatformBridge.PromptTextHandler != null)
            {
                AndroidPlatformBridge.PromptTextHandler(
                    "Buscar en Steam Workshop (texto, ID o URL)",
                    _searchQuery,
                    false,
                    val =>
                    {
                        Container.AddScheduledUpdate(() =>
                        {
                            _searchQuery = val?.Trim() ?? string.Empty;
                            _searchLabel.Text = string.IsNullOrEmpty(_searchQuery)
                                ? "Buscar mapa, skin, plugin o pegar ID / URL..."
                                : _searchQuery;
                            _page = 1;
                            RefreshCurrentQuery();
                        });
                    });
            }
            else
            {
                DialogManager.Show(new YesNoTextDialog("BUSCAR WORKSHOP", "Introduce texto, ID o URL de Workshop:",
                    _searchQuery, "Ej: 2806194402 o nombre de skin", val =>
                    {
                        _searchQuery = val?.Trim() ?? string.Empty;
                        _searchLabel.Text = string.IsNullOrEmpty(_searchQuery)
                            ? "Buscar mapa, skin, plugin o pegar ID / URL..."
                            : _searchQuery;
                        _page = 1;
                        RefreshCurrentQuery();
                    }));
            }
        }

        private void RefreshCurrentQuery()
        {
            try { _queryCts?.Cancel(); } catch { }
            _queryCts = new CancellationTokenSource();
            var ct = _queryCts.Token;

            _loadingWheel.Visible = true;
            _emptyNoticeText.Visible = false;
            _pageLabel.Text = $"Pág {_page}";

            var mode = _mode;
            var sort = _sort;
            var search = _searchQuery;
            var page = _page;

            Task.Run(async () =>
            {
                var res = await SteamWorkshopService.Instance.QueryWorkshopAsync(mode, sort, search, page, ct).ConfigureAwait(false);
                if (ct.IsCancellationRequested)
                    return;

                Container.AddScheduledUpdate(() =>
                {
                    if (ct.IsCancellationRequested)
                        return;

                    _loadingWheel.Visible = false;
                    _total = res.Total;
                    _hasMore = res.HasMore;
                    _pageLabel.Text = _total > 0 ? $"Pág {_page} ({_total})" : $"Pág {_page}";
                    PopulateList(res.Items, res.Notice);
                    UpdateAuthBanner();
                });
            }, ct);
        }

        private void PopulateList(List<WorkshopItemInfo> items, string notice)
        {
            foreach (var old in _cards)
            {
                _scrollContainer.RemoveContainedDrawable(old);
                old.Destroy();
            }
            _cards.Clear();
            _scrollContainer.TargetY = 0;

            if (items == null || items.Count == 0)
            {
                _emptyNoticeText.Text = string.IsNullOrEmpty(notice)
                    ? "No se encontraron resultados."
                    : notice;
                _emptyNoticeText.Visible = true;
                _scrollContainer.ContentContainer.Height = _scrollContainer.Height;
                return;
            }

            _emptyNoticeText.Visible = false;
            const float rowH = 114f;
            const float gap = 10f;
            var cardW = _scrollContainer.Width - 18f;

            for (var i = 0; i < items.Count; i++)
            {
                var item = items[i];
                var card = new WorkshopClippedButton(_scrollContainer, _scrollContainer, WobbleAssets.WhiteBox, (o, e) =>
                {
                    UpdateDetailPanel(item);
                })
                {
                    Size = new ScalableVector2(cardW, rowH),
                    Position = new ScalableVector2(4, i * (rowH + gap) + 4f),
                    Tint = ColorHelper.HexToColor("#1A1F2E")
                };
                card.AddBorder(_selectedItem?.PublishedFileId == item.PublishedFileId
                    ? ColorHelper.HexToColor("#3B82F6")
                    : ColorHelper.HexToColor("#2A324B"), 2);

                var thumb = new Sprite
                {
                    Parent = card,
                    Alignment = Alignment.MidLeft,
                    Position = new ScalableVector2(10, 0),
                    Size = new ScalableVector2(166, 94),
                    Image = UserInterface.DefaultBanner
                };
                LoadThumbAsync(item.PreviewUrl, tex => thumb.Image = tex);

                var titleTxt = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterBold), item.Title, 20)
                {
                    Parent = card,
                    Position = new ScalableVector2(190, 14),
                    Tint = Color.White
                };
                titleTxt.TruncateWithEllipsis((int)Math.Max(180, cardW - 220));

                var tagsStr = item.Tags.Count > 0 ? string.Join(", ", item.Tags) : (item.FileType == 2 ? "Colección" : "Workshop");
                var sizeStr = item.FileSize > 0 ? SteamWorkshopService.FormatBytes(item.FileSize) : "CDN";
                var infoStr = $"ID: {item.PublishedFileId}  |  {tagsStr}  |  {sizeStr}  |  {item.Subscriptions} subs";
                new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterRegular), infoStr, 15)
                {
                    Parent = card,
                    Position = new ScalableVector2(190, 48),
                    Tint = ColorHelper.HexToColor("#93C5FD")
                };

                var badgeStr = item.IsInstalled ? $"[INSTALADO - {item.InstalledCategory ?? "Local"}]" : item.ShortDescription;
                var subTxt = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterRegular), badgeStr, 14)
                {
                    Parent = card,
                    Position = new ScalableVector2(190, 76),
                    Tint = item.IsInstalled ? ColorHelper.HexToColor("#4ADE80") : ColorHelper.HexToColor("#94A3B8")
                };
                subTxt.TruncateWithEllipsis((int)Math.Max(180, cardW - 220));

                _scrollContainer.AddContainedDrawable(card);
                _cards.Add(card);
            }

            _scrollContainer.ContentContainer.Height = Math.Max(_scrollContainer.Height, items.Count * (rowH + gap) + 12f);

            if (_selectedItem == null && items.Count > 0)
                UpdateDetailPanel(items[0]);
        }

        private void UpdateDetailPanel(WorkshopItemInfo item)
        {
            _selectedItem = item;
            if (item == null)
            {
                _detailThumb.Image = UserInterface.DefaultBanner;
                _detailTitle.Text = "Selecciona un elemento";
                _detailMeta.Text = "";
                _detailDesc.Text = "Toca cualquier elemento de la lista para ver detalles, suscribirte o descargarlo directamente a Android.";
                _downloadBtn.Visible = false;
                _applySkinBtn.Visible = false;
                _subscribeBtn.Visible = false;
                _openWebBtn.Visible = false;
                _deleteLocalBtn.Visible = false;
                return;
            }

            _detailThumb.Image = UserInterface.DefaultBanner;
            LoadThumbAsync(item.PreviewUrl, tex =>
            {
                if (_selectedItem?.PublishedFileId == item.PublishedFileId)
                    _detailThumb.Image = tex;
            });

            _detailTitle.Text = item.Title;
            var tagsStr = item.Tags.Count > 0 ? string.Join(", ", item.Tags) : "General";
            _detailMeta.Text = $"ID {item.PublishedFileId}  |  {tagsStr}  |  {(item.FileSize > 0 ? SteamWorkshopService.FormatBytes(item.FileSize) : "CDN")}  |  {item.Subscriptions} subs";
            _detailDesc.Text = string.IsNullOrWhiteSpace(item.ShortDescription)
                ? "Sin descripción corta."
                : (item.ShortDescription.Length > 260 ? item.ShortDescription.Substring(0, 260) + "..." : item.ShortDescription);

            _detailDestInfo.Text = item.IsInstalled
                ? $"Instalado en: {item.LocalInstallPath}"
                : "Destino Android: Workshop/<ID>/ (Skins/Plugins) o Songs/ (Mapas)";

            _downloadBtn.Visible = true;
            _openWebBtn.Visible = true;
            _subscribeBtn.Visible = true;
            _applySkinBtn.Visible = item.InstalledHasSkin;
            _deleteLocalBtn.Visible = item.IsInstalled;

            if (!_isDownloading)
                _downloadBtnLabel.Text = item.IsInstalled ? "REINSTALAR / ACTUALIZAR" : "DESCARGAR E INSTALAR";
        }

        private void StartDownloadOrCancel()
        {
            if (_isDownloading)
            {
                try { _downloadCts?.Cancel(); } catch { }
                return;
            }

            if (_selectedItem == null)
                return;

            var target = _selectedItem;
            _isDownloading = true;
            _downloadCts = new CancellationTokenSource();
            var ct = _downloadCts.Token;

            _downloadBtnLabel.Text = "CANCELAR DESCARGA";
            _downloadBtn.Tint = ColorHelper.HexToColor("#B91C1C");
            _progressFill.Width = 0;
            _progressLabel.Text = "Iniciando descarga Steam3...";

            Task.Run(async () =>
            {
                var res = await SteamWorkshopService.Instance.DownloadAndInstallAsync(target, (pct, status) =>
                {
                    Container.AddScheduledUpdate(() =>
                    {
                        _progressFill.Width = _progressBg.Width * Math.Clamp(pct, 0f, 1f);
                        _progressLabel.Text = status ?? "";
                    });
                }, ct).ConfigureAwait(false);

                Container.AddScheduledUpdate(() =>
                {
                    _isDownloading = false;
                    _downloadBtn.Tint = ColorHelper.HexToColor("#16A34A");
                    _progressFill.Width = res.Success ? _progressBg.Width : 0;
                    _progressLabel.Text = res.Message;

                    if (res.Success)
                    {
                        NotificationManager.Show(NotificationLevel.Success, res.Message);
                        if (res.QueuedMaps)
                            _importMapsBtn.Visible = MapsetImporter.Queue.Count > 0;
                        UpdateDetailPanel(target);
                        RefreshCurrentQuery();
                    }
                    else
                    {
                        NotificationManager.Show(NotificationLevel.Error, res.Message);
                        _downloadBtnLabel.Text = target.IsInstalled ? "REINSTALAR / ACTUALIZAR" : "DESCARGAR E INSTALAR";
                    }
                });
            }, ct);
        }

        private void ApplySelectedSkin()
        {
            if (_selectedItem == null)
                return;
            if (SteamWorkshopService.Instance.TryApplyWorkshopSkin(_selectedItem.PublishedFileId))
                NotificationManager.Show(NotificationLevel.Success, $"Skin aplicado: {_selectedItem.Title}");
            else
                NotificationManager.Show(NotificationLevel.Warning, "Este elemento no contiene skin.ini / skin.yml");
        }

        private void ToggleSubscribe()
        {
            if (_selectedItem == null)
                return;
            if (!SteamWorkshopService.Instance.IsAuthenticated)
            {
                DialogManager.Show(new SteamAuthDialog(() => RefreshCurrentQuery()));
                return;
            }

            var id = _selectedItem.PublishedFileId;
            Task.Run(async () =>
            {
                var (ok, msg) = await SteamWorkshopService.Instance.SetSubscribedAsync(id, true).ConfigureAwait(false);
                Container.AddScheduledUpdate(() =>
                {
                    NotificationManager.Show(ok ? NotificationLevel.Success : NotificationLevel.Error, msg);
                });
            });
        }

        private void DeleteSelectedLocal()
        {
            if (_selectedItem == null)
                return;
            if (SteamWorkshopService.Instance.DeleteLocalItem(_selectedItem.PublishedFileId))
            {
                NotificationManager.Show(NotificationLevel.Info, "Elemento eliminado de almacenamiento local.");
                _selectedItem.IsInstalled = false;
                _selectedItem.InstalledHasSkin = false;
                UpdateDetailPanel(_selectedItem);
                RefreshCurrentQuery();
            }
        }

        private void LoadThumbAsync(string url, Action<Texture2D> onLoaded)
        {
            if (string.IsNullOrWhiteSpace(url))
                return;

            if (_thumbCache.TryGetValue(url, out var cached))
            {
                onLoaded?.Invoke(cached);
                return;
            }

            Task.Run(async () =>
            {
                var bytes = await SteamWorkshopService.Instance.DownloadImageBytesAsync(url).ConfigureAwait(false);
                if (bytes == null || bytes.Length == 0)
                    return;

                Container.AddScheduledUpdate(() =>
                {
                    try
                    {
                        if (!_thumbCache.TryGetValue(url, out var tex))
                        {
                            tex = AssetLoader.LoadTexture2D(bytes);
                            _thumbCache[url] = tex;
                        }
                        onLoaded?.Invoke(tex);
                    }
                    catch
                    {
                    }
                });
            });
        }

        public override void Update(GameTime gameTime) => Container?.Update(gameTime);

        public override void Draw(GameTime gameTime)
        {
            GameBase.Game.GraphicsDevice.Clear(ColorHelper.HexToColor("#0E111A"));
            Container?.Draw(gameTime);
        }

        public override void Destroy()
        {
            SteamWorkshopService.Instance.AuthStateChanged -= OnServiceAuthChanged;
            try { _queryCts?.Cancel(); } catch { }
            try { _downloadCts?.Cancel(); } catch { }
            Container?.Destroy();
            foreach (var tex in _thumbCache.Values)
            {
                try { tex?.Dispose(); } catch { }
            }
            _thumbCache.Clear();
        }

        private static ImageButton MakeButton(Drawable parent, string text, ScalableVector2 size, Color fill, Color border, EventHandler onClick)
        {
            var btn = new ImageButton(WobbleAssets.WhiteBox, onClick)
            {
                Parent = parent,
                Size = size,
                Tint = fill
            };
            btn.AddBorder(border, 2);
            var lbl = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), text, 17)
            {
                Parent = btn,
                Alignment = Alignment.MidCenter,
                Tint = Color.White
            };
            lbl.TruncateWithEllipsis((int)Math.Max(40, size.X.Value - 16));
            return btn;
        }

        private static SpriteTextPlus GetButtonText(Drawable btn)
        {
            foreach (var c in btn.Children)
            {
                if (c is SpriteTextPlus st)
                    return st;
            }
            return null;
        }
    }
} 
""",
    encoding="utf-8",
) 
# 20) ImGui seguro en Android (ImGuiSupport + SpriteImGui + EditScreenView con barra tactil Guardar/Probar/Salir)
imgui_support_cs = root / "Wobble" / "Wobble" / "Graphics" / "ImGUI" / "ImGuiSupport.cs"
if imgui_support_cs.parent.is_dir():
    imgui_support_cs.write_text(
        """using System;
using System.Runtime.InteropServices;

namespace Wobble.Graphics.ImGUI
{
    public static class ImGuiSupport
    {
        private static int _state; // 0 = unchecked, 1 = available, -1 = unavailable

        public static bool IsAvailable
        {
            get
            {
                if (_state != 0)
                    return _state == 1;

                try
                {
                    if (OperatingSystem.IsAndroid())
                    {
                        if (NativeLibrary.TryLoad("libcimgui.so", out var h1) || NativeLibrary.TryLoad("cimgui", out h1))
                        {
                            _state = 1;
                            return true;
                        }
                        _state = -1;
                        return false;
                    }
                    _state = 1;
                    return true;
                }
                catch
                {
                    _state = -1;
                    return false;
                }
            }
        }
    }
}
""",
        encoding="utf-8",
    )

sprite_imgui_cs = root / "Wobble" / "Wobble" / "Graphics" / "ImGUI" / "SpriteImGui.cs"
if sprite_imgui_cs.is_file():
    sit = sprite_imgui_cs.read_text(encoding="utf-8-sig")
    if "ImGuiSupport.IsAvailable" not in sit:
        sit = sit.replace(
            "        public bool WasActivatedByMouse => Renderer.WasActivatedByMouse;",
            "        public bool WasActivatedByMouse => Renderer != null && Renderer.WasActivatedByMouse;",
            1,
        ).replace(
            "        public bool IsMouseHovered => Renderer.IsMouseHovered;",
            "        public bool IsMouseHovered => Renderer != null && Renderer.IsMouseHovered;",
            1,
        ).replace(
            "        public bool IsMouseInputOwner => Renderer.IsMouseInputOwner;",
            "        public bool IsMouseInputOwner => Renderer != null && Renderer.IsMouseInputOwner;",
            1,
        ).replace(
            "        public bool IsKeyboardInputOwner => Renderer.IsKeyboardInputOwner;",
            "        public bool IsKeyboardInputOwner => Renderer != null && Renderer.IsKeyboardInputOwner;",
            1,
        ).replace(
            "        public bool WantsMouseInput => Renderer.WantsMouseInput;",
            "        public bool WantsMouseInput => Renderer != null && Renderer.WantsMouseInput;",
            1,
        ).replace(
            "        public bool WantsKeyboardInput => Renderer.WantsKeyboardInput;",
            "        public bool WantsKeyboardInput => Renderer != null && Renderer.WantsKeyboardInput;",
            1,
        ).replace(
            "        public bool WantsTextInput => Renderer.WantsTextInput;",
            "        public bool WantsTextInput => Renderer != null && Renderer.WantsTextInput;",
            1,
        ).replace(
            "            Options = options;\n\n            if (Thread.CurrentThread.ManagedThreadId == GameBase.Game.MainThreadId)",
            "            Options = options;\n            if (!ImGuiSupport.IsAvailable)\n                return;\n\n            if (Thread.CurrentThread.ManagedThreadId == GameBase.Game.MainThreadId)",
            1,
        ).replace(
            "        public virtual void Draw(GameTime gameTime)\n        {\n            if (ImGui.GetCurrentContext() != Renderer.Context)",
            "        public virtual void Draw(GameTime gameTime)\n        {\n            if (Renderer == null)\n                return;\n\n            if (ImGui.GetCurrentContext() != Renderer.Context)",
            1,
        ).replace(
            "        public virtual void Destroy() => Renderer.Dispose();",
            "        public virtual void Destroy() => Renderer?.Dispose();",
            1,
        )
        sprite_imgui_cs.write_text(sit, encoding="utf-8")

esv_cs = root / "Quaver.Shared" / "Screens" / "Edit" / "EditScreenView.cs"
if esv_cs.is_file():
    esvt = esv_cs.read_text(encoding="utf-8-sig")
    if "CreateAndroidEditorBar" not in esvt:
        esvt = esvt.replace(
            "using Wobble.Window;",
            "using Wobble.Window;\nusing Wobble.Graphics.Sprites.Text;\nusing Wobble.Managers;\nusing Quaver.Shared.Graphics.Notifications;",
            1,
        )
        esvt = esvt.replace(
            "            Footer.Parent = Container;",
            "            Footer.Parent = Container;\n\n            if (!ImGuiSupport.IsAvailable)\n                CreateAndroidEditorBar();",
            1,
        )
        old_esv_draw = """            if (MenuBar != null && !EditScreen.Exiting)
            {
                if (DialogManager.Dialogs.Count == 0)
                    DrawPlugins(gameTime);

                MenuBar?.Draw(gameTime);
                GameBase.Game.TryEndBatch();

                if (ImGui.IsAnyItemHovered() || ImGui.IsAnyItemActive() || ImGui.IsAnyItemFocused())
                {
                    IsImGuiMouseCaptured = true;
                    IsImGuiKeyboardCaptured = true;
                }
            }"""
        new_esv_draw = """            if (ImGuiSupport.IsAvailable && MenuBar != null && !EditScreen.Exiting)
            {
                if (DialogManager.Dialogs.Count == 0)
                    DrawPlugins(gameTime);

                MenuBar?.Draw(gameTime);
                GameBase.Game.TryEndBatch();

                if (ImGui.IsAnyItemHovered() || ImGui.IsAnyItemActive() || ImGui.IsAnyItemFocused())
                {
                    IsImGuiMouseCaptured = true;
                    IsImGuiKeyboardCaptured = true;
                }
            }"""
        esvt = esvt.replace(old_esv_draw, new_esv_draw, 1)
        old_dp = "                if (ImGui.IsAnyItemHovered() || plugin.IsWindowHovered)"
        new_dp = "                if ((ImGuiSupport.IsAvailable && ImGui.IsAnyItemHovered()) || plugin.IsWindowHovered)"
        esvt = esvt.replace(old_dp, new_dp, 1)
        esvt = esvt.replace(
            "        private void CreateBackground()",
            """        private void CreateAndroidEditorBar()
        {
            var topY = 12f + Math.Max(0, WindowManager.Height * global::Wobble.Platform.AndroidPlatformBridge.SafeInsetTop);
            var bar = new Sprite
            {
                Parent = Container,
                Alignment = Alignment.TopCenter,
                Y = topY,
                Size = new ScalableVector2(540, 50),
                Tint = new Color(18, 22, 34, 220)
            };
            bar.AddBorder(new Color(69, 214, 245), 2);

            void AddBarButton(string label, float x, Color fill, EventHandler onClick)
            {
                var btn = new ImageButton(UserInterface.BlankBox, onClick)
                {
                    Parent = bar,
                    Alignment = Alignment.MidLeft,
                    X = x,
                    Size = new ScalableVector2(166, 38),
                    Tint = fill
                };
                btn.AddBorder(new Color(90, 110, 145), 1);
                var txt = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), label, 16)
                {
                    Parent = btn,
                    Alignment = Alignment.MidCenter,
                    Tint = Color.White
                };
            }

            AddBarButton("GUARDAR", 10, new Color(36, 130, 82), (s, e) =>
            {
                try
                {
                    EditScreen.Save(true);
                    NotificationManager.Show(NotificationLevel.Success, "Mapa guardado");
                }
                catch (Exception ex)
                {
                    NotificationManager.Show(NotificationLevel.Error, "Error al guardar: " + ex.Message);
                }
            });

            AddBarButton("PROBAR", 187, new Color(36, 104, 168), (s, e) =>
            {
                try { EditScreen.ExitToTestPlay(false); } catch { }
            });

            AddBarButton("SALIR", 364, new Color(156, 48, 56), (s, e) =>
            {
                try { EditScreen.LeaveEditor(); } catch { }
            });
        }

        private void CreateBackground()""",
            1,
        )
        esv_cs.write_text(esvt, encoding="utf-8")

# 21) Wobble MouseManager (snapshot unico TouchPanel + drag scroll + suppress en gameplay) y KeyboardManager (menu nav virtual keys)
mm_cs = root / "Wobble" / "Wobble" / "Input" / "MouseManager.cs"
if mm_cs.is_file():
    mmt = mm_cs.read_text(encoding="utf-8-sig")
    if "UpdateTouchSnapshot" not in mmt:
        if "using Wobble.Platform;" not in mmt:
            mmt = mmt.replace(
                "using Microsoft.Xna.Framework.Input;",
                "using Microsoft.Xna.Framework.Input;\nusing Wobble.Platform;\nusing Wobble.Window;",
                1,
            )
        if "using Microsoft.Xna.Framework.Input.Touch;" not in mmt:
            mmt = mmt.replace(
                "using Microsoft.Xna.Framework.Input;",
                "using Microsoft.Xna.Framework.Input;\nusing Microsoft.Xna.Framework.Input.Touch;",
                1,
            )
        old_priv_mm = "        private static EnhancedMouseState SyntheticState { get; set; }"
        new_priv_mm = """        private static EnhancedMouseState SyntheticState { get; set; }
        private static int _touchScrollAccum;
        private static int _activeScrollTouchId = -1;
        private static float _lastScrollTouchY;
        private static bool _isDragScrolling;
        private static int _dragStartTouchId = -1;
        private static Vector2 _dragStartPos;"""
        mmt = mmt.replace(old_priv_mm, new_priv_mm, 1)

        mmt = re.sub(
            r"        internal static void Update\(\).*?(?=\n        /// <summary>\s*\n\s*///\s*Enables deterministic input)",
            """        internal static void Update()
        {
            PreviousState = CurrentState;
            if (IsSyntheticInputEnabled)
            {
                CurrentState = SyntheticState;
                return;
            }

            if (global::System.OperatingSystem.IsAndroid())
            {
                var touches = TouchPanel.GetState();
                AndroidPlatformBridge.UpdateTouchSnapshot(touches);

                if (AndroidPlatformBridge.SuppressMouseFromTouch)
                {
                    _touchWasDown = false;
                    _activeScrollTouchId = -1;
                    _dragStartTouchId = -1;
                    _isDragScrolling = false;
                    CurrentState = new EnhancedMouseState(
                        PreviousState.Position,
                        _touchScrollAccum,
                        ButtonState.Released,
                        ButtonState.Released,
                        ButtonState.Released,
                        ButtonState.Released,
                        ButtonState.Released
                    );
                    return;
                }

                TouchLocation? primary = null;
                for (var i = 0; i < touches.Count; i++)
                {
                    if (touches[i].State != TouchLocationState.Invalid)
                    {
                        primary = touches[i];
                        break;
                    }
                }

                if (primary.HasValue)
                {
                    var t = primary.Value;
                    var px = t.Position.X;
                    var py = t.Position.Y;
                    var gd = GameBase.Game?.GraphicsDevice;
                    if (gd != null && TouchPanel.DisplayWidth > 0 && TouchPanel.DisplayHeight > 0)
                    {
                        px = px * gd.PresentationParameters.BackBufferWidth / TouchPanel.DisplayWidth;
                        py = py * gd.PresentationParameters.BackBufferHeight / TouchPanel.DisplayHeight;
                    }
                    var scale = WindowManager.ScreenScale;
                    var sx = scale.X > 0.001f ? scale.X : 1f;
                    var sy = scale.Y > 0.001f ? scale.Y : 1f;
                    var pos = new Vector2(px / sx, py / sy);

                    if (t.State == TouchLocationState.Pressed || _dragStartTouchId != t.Id)
                    {
                        _dragStartTouchId = t.Id;
                        _dragStartPos = pos;
                        _isDragScrolling = false;
                        _activeScrollTouchId = t.Id;
                        _lastScrollTouchY = pos.Y;
                    }
                    else if (t.State == TouchLocationState.Moved)
                    {
                        var dyFromStart = pos.Y - _dragStartPos.Y;
                        if (!_isDragScrolling && Math.Abs(dyFromStart) > 22f)
                            _isDragScrolling = true;

                        if (_isDragScrolling && _activeScrollTouchId == t.Id)
                        {
                            var dy = pos.Y - _lastScrollTouchY;
                            _lastScrollTouchY = pos.Y;
                            var step = (int)Math.Round(dy * 2.2f);
                            if (step != 0)
                                _touchScrollAccum += step;
                        }
                    }

                    var isDown = t.State != TouchLocationState.Released && !_isDragScrolling;
                    _touchWasDown = isDown;
                    _lastTouchPoint = new Point((int)px, (int)py);
                    CurrentState = new EnhancedMouseState(
                        pos,
                        _touchScrollAccum,
                        isDown ? ButtonState.Pressed : ButtonState.Released,
                        ButtonState.Released,
                        ButtonState.Released,
                        ButtonState.Released,
                        ButtonState.Released
                    );
                    if (t.State == TouchLocationState.Released)
                    {
                        _activeScrollTouchId = -1;
                        _dragStartTouchId = -1;
                        _isDragScrolling = false;
                    }
                    return;
                }

                _touchWasDown = false;
                _activeScrollTouchId = -1;
                _dragStartTouchId = -1;
                _isDragScrolling = false;
                var msNoTouch = Mouse.GetState();
                CurrentState = new EnhancedMouseState(
                    PreviousState.Position,
                    _touchScrollAccum + msNoTouch.ScrollWheelValue,
                    msNoTouch.LeftButton,
                    msNoTouch.RightButton,
                    msNoTouch.MiddleButton,
                    msNoTouch.XButton1,
                    msNoTouch.XButton2
                );
                return;
            }

            CurrentState = new EnhancedMouseState(Mouse.GetState());
        }""",
            mmt,
            count=1,
            flags=re.S,
        )
        mm_cs.write_text(mmt, encoding="utf-8")

km_cs = root / "Wobble" / "Wobble" / "Input" / "KeyboardManager.cs"
if km_cs.is_file():
    kmt = km_cs.read_text(encoding="utf-8-sig")
    if "GetMenuNavVirtualKeysHandler" not in kmt:
        kmt = kmt.replace(
            "using Wobble.Bindables;",
            "using Wobble.Bindables;\nusing Wobble.Platform;",
            1,
        )
        old_km_upd = """        internal static void Update()
        {
            PreviousState = CurrentState;
            CurrentState = Keyboard.GetState();
        }"""
        new_km_upd = """        internal static void Update()
        {
            PreviousState = CurrentState;
            var ks = Keyboard.GetState();
            if (OperatingSystem.IsAndroid())
            {
                var extra = AndroidPlatformBridge.GetMenuNavVirtualKeysHandler?.Invoke();
                var hasExtra = extra != null && extra.Length > 0;
                if (hasExtra || AndroidPlatformBridge.IsNativeBackPressed)
                {
                    var list = new List<Keys>(ks.GetPressedKeys());
                    if (AndroidPlatformBridge.IsNativeBackPressed && !list.Contains(Keys.Escape))
                        list.Add(Keys.Escape);
                    if (hasExtra)
                    {
                        foreach (var k in extra)
                        {
                            if (k != Keys.None && !list.Contains(k))
                                list.Add(k);
                        }
                    }
                    CurrentState = new KeyboardState(list.ToArray());
                    return;
                }
            }
            CurrentState = ks;
        }"""
        kmt = kmt.replace(old_km_upd, new_km_upd, 1)
        km_cs.write_text(kmt, encoding="utf-8")

# 24) Menu de Opciones "Android Controls" (Tactil + Remapeo Mando + Deadzone + Vibracion)
opt_custom_dir = root / "Quaver.Shared" / "Screens" / "Options" / "Items" / "Custom"
(opt_custom_dir / "OptionsItemGamepadBind.cs").write_text(
    """using Microsoft.Xna.Framework;
using MonoGame.Extended;
using Quaver.Shared.Assets;
using Quaver.Shared.Graphics;
using Quaver.Shared.Input.Android;
using Wobble.Graphics;
using Wobble.Graphics.Sprites.Text;
using Wobble.Graphics.UI.Buttons;
using Wobble.Managers;
using ColorHelper = Quaver.Shared.Helpers.ColorHelper;

namespace Quaver.Shared.Screens.Options.Items.Custom
{
    public class OptionsItemGamepadBind : OptionsItem
    {
        private readonly int _keyCount;
        private readonly int _lane;
        private readonly ImageButton _button;
        private readonly SpriteTextPlus _text;

        public OptionsItemGamepadBind(RectangleF containerRect, string name, int keyCount, int lane)
            : base(containerRect, name)
        {
            _keyCount = keyCount;
            _lane = lane;

            _button = new ImageButton(UserInterface.DropdownClosed)
            {
                Parent = this,
                Alignment = Alignment.MidRight,
                X = -Name.X,
                Size = new ScalableVector2(250, 35),
                Tint = ColorHelper.HexToColor("#181818"),
                UsePreviousSpriteBatchOptions = true
            };

            _text = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "", 18)
            {
                Parent = _button,
                Alignment = Alignment.MidCenter,
                Tint = Colors.MainAccent,
                UsePreviousSpriteBatchOptions = true
            };

            RefreshText();

            _button.Clicked += (s, e) =>
            {
                Focused = true;
                _text.Text = "PRESS BUTTON...";
                _text.Tint = Color.Yellow;
                AndroidControlsManager.Instance.BeginButtonCapture(btn =>
                {
                    AndroidControlsManager.Instance.SetGamepadBindingForLane(_keyCount, _lane, btn);
                    Focused = false;
                    RefreshText();
                });
            };

            _button.ClickedOutside += (s, e) =>
            {
                if (Focused)
                {
                    AndroidControlsManager.Instance.CancelButtonCapture();
                    Focused = false;
                    RefreshText();
                }
            };
        }

        public void RefreshText()
        {
            var bound = AndroidControlsManager.Instance.GetGamepadBindingForLane(_keyCount, _lane);
            _text.Text = AndroidControlsManager.FormatButtonLabel(bound);
            _text.Tint = Colors.MainAccent;
        }
    }
}
""",
    encoding="utf-8",
)

(opt_custom_dir / "OptionsItemActionButton.cs").write_text(
    """using System;
using Microsoft.Xna.Framework;
using MonoGame.Extended;
using Quaver.Shared.Assets;
using Wobble.Graphics;
using Wobble.Graphics.Sprites.Text;
using Wobble.Graphics.UI.Buttons;
using Wobble.Managers;
using ColorHelper = Quaver.Shared.Helpers.ColorHelper;

namespace Quaver.Shared.Screens.Options.Items.Custom
{
    public class OptionsItemActionButton : OptionsItem
    {
        public OptionsItemActionButton(RectangleF containerRect, string name, string buttonLabel, Action onClick)
            : base(containerRect, name)
        {
            var btn = new ImageButton(UserInterface.BlankBox, (s, e) => onClick?.Invoke())
            {
                Parent = this,
                Alignment = Alignment.MidRight,
                X = -Name.X,
                Size = new ScalableVector2(250, 36),
                Tint = ColorHelper.HexToColor("#1A5D8A"),
                UsePreviousSpriteBatchOptions = true
            };
            btn.AddBorder(ColorHelper.HexToColor("#45D6F5"), 1);

            var lbl = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), buttonLabel, 17)
            {
                Parent = btn,
                Alignment = Alignment.MidCenter,
                Tint = Color.White,
                UsePreviousSpriteBatchOptions = true
            };
        }
    }
}
""",
    encoding="utf-8",
)

om_cs = root / "Quaver.Shared" / "Screens" / "Options" / "OptionsMenu.cs"
if om_cs.is_file():
    omt = om_cs.read_text(encoding="utf-8-sig")
    if "Android Controls" not in omt:
        omt = omt.replace(
            "using Quaver.Shared.Input.Global;",
            "using Quaver.Shared.Input.Global;\nusing Quaver.Shared.Input.Android;\nusing Quaver.Shared.Graphics.Notifications;\nusing Quaver.Shared.Graphics.Form.Dropdowns;",
            1,
        )
        old_om_end = """            SelectedSection = new Bindable<OptionsSection>(Sections.First()) { Value = Sections.First() };
        }"""
        new_om_end = """            var ctrl = AndroidControlsManager.Instance;
            ctrl.Initialize();

            var bind4Items = new List<OptionsItem>();
            for (var li = 0; li < 4; li++)
                bind4Items.Add(new OptionsItemGamepadBind(containerRect, $"4K Lane {li + 1} Gamepad Button", 4, li));

            var presetDd = new Dropdown(
                new List<string>(ctrl.GetGamepad4KPresetNames()),
                new ScalableVector2(250, 35),
                17,
                selectedIndex: ctrl.GetCurrent4KPresetIndex()
            );
            presetDd.ItemSelected += (s, e) =>
            {
                ctrl.Apply4KPreset(e.Index);
                foreach (var item in bind4Items)
                {
                    if (item is OptionsItemGamepadBind gb)
                        gb.RefreshText();
                }
            };

            var gamepadItems = new List<OptionsItem>
            {
                new OptionsItemCheckbox(containerRect, "Enable Gamepad Input", ctrl.GamepadEnabledBindable),
                new OptionsItemDropdown(containerRect, "4K Gamepad Preset", presetDd),
            };
            gamepadItems.AddRange(bind4Items);
            gamepadItems.Add(new OptionsSlider(containerRect, "Gamepad Stick Deadzone", ctrl.GamepadDeadzoneBindable, v => $"{v}%"));
            gamepadItems.Add(new OptionsItemCheckbox(containerRect, "Gamepad Hit Vibration", ctrl.GamepadVibrationEnabledBindable));
            gamepadItems.Add(new OptionsSlider(containerRect, "Vibration Intensity", ctrl.GamepadVibrationIntensityBindable, v => $"{v}%"));
            gamepadItems.Add(new OptionsItemActionButton(containerRect, "Reset Touch & Gamepad Controls", "RESET DEFAULTS", () =>
            {
                ctrl.ResetAllToDefaults();
                foreach (var item in bind4Items)
                {
                    if (item is OptionsItemGamepadBind gb)
                        gb.RefreshText();
                }
                NotificationManager.Show(NotificationLevel.Success, "Controles Android restablecidos");
            }));

            Sections.Add(new OptionsSection("Android Controls", UserInterface.OptionsInput, new List<OptionsSubcategory>
            {
                new OptionsSubcategory("Touchscreen Gameplay", new List<OptionsItem>
                {
                    new OptionsItemCheckbox(containerRect, "Enable Touch Controls", ctrl.TouchEnabledBindable),
                    new OptionsSlider(containerRect, "Touch Zone Height", ctrl.TouchHeightPercentBindable, v => $"{v}%"),
                    new OptionsSlider(containerRect, "Touch Bottom Margin", ctrl.TouchMarginBottomBindable, v => $"{v} px"),
                    new OptionsSlider(containerRect, "Touch Lane Spacing", ctrl.TouchSpacingBindable, v => $"{v} px"),
                    new OptionsSlider(containerRect, "Touch Overlay Opacity", ctrl.TouchOpacityPercentBindable, v => $"{v}%"),
                    new OptionsItemCheckbox(containerRect, "Touch Edge Guard (Safe Margins)", ctrl.TouchEdgeGuardBindable),
                    new OptionsItemCheckbox(containerRect, "Show Touch Lane Labels", ctrl.TouchShowLabelsBindable),
                    new OptionsItemCheckbox(containerRect, "Touch Hit Vibration", ctrl.TouchVibrationEnabledBindable),
                }),
                new OptionsSubcategory("Gamepad (Bluetooth / USB HID)", gamepadItems)
            }));

            SelectedSection = new Bindable<OptionsSection>(Sections.First()) { Value = Sections.First() };
        }"""
        omt = omt.replace(old_om_end, new_om_end, 1)
        om_cs.write_text(omt, encoding="utf-8")
        # 22) AndroidControlsManager (Touch Multitouch 1K-10K + Mando HID/BT/USB + Config + Vibracion)
android_input_dir = root / "Quaver.Shared" / "Input" / "Android"
android_input_dir.mkdir(parents=True, exist_ok=True)
(android_input_dir / "AndroidControlsManager.cs").write_text(
    """using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.Xna.Framework;
using Microsoft.Xna.Framework.Input;
using Microsoft.Xna.Framework.Input.Touch;
using MonoGame.Extended;
using Newtonsoft.Json;
using Quaver.API.Enums;
using Wobble;
using Wobble.Bindables;
using Wobble.Platform;
using Wobble.Window;

namespace Quaver.Shared.Input.Android
{
    public sealed class AndroidControlsManager
    {
        
        private const int MaxLanes = 10;
        private const int StickLeft = 1001, StickRight = 1002, StickUp = 1003, StickDown = 1004;

        private static readonly string[] Preset4KNames =
        {
            "D-Pad + Face (Left/Down/X/B)",
            "Shoulders + Triggers (L2/L1/R1/R2)",
            "DJMAX Layout (Left/Up/Y/B)",
            "D-Pad Alt (Left/Right/X/B)"
        };

        private static readonly int[][] Preset4KButtons =
        {
            new[] { 21, 20, 99, 97 },
            new[] { 104, 102, 103, 105 },
            new[] { 21, 19, 100, 97 },
            new[] { 21, 22, 99, 97 }
        };

        private static readonly int[] GenericDefaults = { 21, 20, 19, 22, 104, 102, 103, 105, 99, 97 };
        public static AndroidControlsManager Instance { get; } = new AndroidControlsManager();

        private sealed class SavedConfig
        {
            public bool TouchEnabled { get; set; } = true;
            public int TouchHeightPercent { get; set; } = 32;
            public int TouchMarginBottom { get; set; } = 12;
            public int TouchSpacing { get; set; } = 8;
            public int TouchOpacityPercent { get; set; } = 45;
            public bool TouchEdgeGuard { get; set; } = true;
            public bool TouchShowLabels { get; set; } = true;
            public bool TouchVibrationEnabled { get; set; } = true;
            public bool GamepadEnabled { get; set; } = true;
            public int GamepadDeadzone { get; set; } = 22;
            public bool GamepadVibrationEnabled { get; set; } = true;
            public int GamepadVibrationIntensity { get; set; } = 65;
            public Dictionary<int, int[]> GamepadBindings { get; set; } = new Dictionary<int, int[]>();
        }

        public Bindable<bool> TouchEnabledBindable { get; } = new Bindable<bool>(true);
        public BindableInt TouchHeightPercentBindable { get; } = new BindableInt(32, 18, 60);
        public BindableInt TouchMarginBottomBindable { get; } = new BindableInt(12, 0, 160);
        public BindableInt TouchSpacingBindable { get; } = new BindableInt(8, 0, 36);
        public BindableInt TouchOpacityPercentBindable { get; } = new BindableInt(45, 10, 95);
        public Bindable<bool> TouchEdgeGuardBindable { get; } = new Bindable<bool>(true);
        public Bindable<bool> TouchShowLabelsBindable { get; } = new Bindable<bool>(true);
        public Bindable<bool> TouchVibrationEnabledBindable { get; } = new Bindable<bool>(true);
        public Bindable<bool> GamepadEnabledBindable { get; } = new Bindable<bool>(true);
        public BindableInt GamepadDeadzoneBindable { get; } = new BindableInt(22, 5, 60);
        public Bindable<bool> GamepadVibrationEnabledBindable { get; } = new Bindable<bool>(true);
        public BindableInt GamepadVibrationIntensityBindable { get; } = new BindableInt(65, 10, 100);

        private readonly object _lock = new object();
        private readonly Dictionary<int, int[]> _bindings = new Dictionary<int, int[]>();
        private readonly HashSet<int> _nativeButtons = new HashSet<int>();
        private readonly HashSet<int> _axisButtons = new HashSet<int>();
        private readonly HashSet<int> _xnaButtons = new HashSet<int>();
        private readonly HashSet<int> _mergedButtons = new HashSet<int>();
        private readonly HashSet<int> _prevMergedButtons = new HashSet<int>();
        private readonly bool[] _touchLaneDown = new bool[MaxLanes];
        private readonly bool[] _gamepadLaneDown = new bool[MaxLanes];
        private readonly RectangleF[] _touchLaneRects = new RectangleF[MaxLanes];

        private bool _initialized, _suppressSave, _inGameplay, _isPaused;
        private int _activeKeyCount = 4, _pendingCapturedButton = -1;
        private float _zoneLeftX, _zoneRightX, _zoneTopY, _zoneBottomY;
        private bool _touchPauseJustPressed, _gamepadPauseJustPressed;
        private long _lastVibrateTick;
        private Action<int> _captureCallback;

        public RectangleF TouchPauseRect { get; private set; }
        public int ActiveKeyCount => _activeKeyCount;

        private AndroidControlsManager() => ResetBindingsDictionary();

        public void Initialize()
        {
            if (_initialized) return;
            _initialized = true;
            LoadConfig();
            HookBindables();
            AndroidPlatformBridge.OnAfterTouchSnapshotUpdated += OnTouchSnapshotUpdated;
            AndroidPlatformBridge.OnNativeGamepadButton += OnNativeGamepadButton;
            AndroidPlatformBridge.OnNativeGamepadAxes += OnNativeGamepadAxes;
            AndroidPlatformBridge.GetMenuNavVirtualKeysHandler = GetMenuNavVirtualKeys;
            RecomputeTouchLayout();
        }

        public void SetGameplayContext(bool inGameplay, bool isPaused, int keyCount = 0)
        {
            lock (_lock)
            {
                _inGameplay = inGameplay;
                _isPaused = isPaused;
                if (keyCount > 0) _activeKeyCount = Math.Clamp(keyCount, 1, MaxLanes);
                if (!inGameplay || isPaused)
                {
                    Array.Clear(_touchLaneDown, 0, _touchLaneDown.Length);
                    if (!inGameplay) { _touchPauseJustPressed = false; _gamepadPauseJustPressed = false; }
                }
            }
            AndroidPlatformBridge.SuppressMouseFromTouch =
                OperatingSystem.IsAndroid() && inGameplay && !isPaused && TouchEnabledBindable.Value;
            if (inGameplay) RecomputeTouchLayout();
        }

        public void Update(GameTime gameTime)
        {
            if (!_initialized) Initialize();
            Action<int> captureCb = null;
            var capturedCode = -1;
            lock (_lock)
            {
                PollXnaGamepadLocked();
                _prevMergedButtons.Clear();
                foreach (var b in _mergedButtons) _prevMergedButtons.Add(b);
                _mergedButtons.Clear();
                if (GamepadEnabledBindable.Value)
                {
                    foreach (var b in _nativeButtons) _mergedButtons.Add(b);
                    foreach (var b in _axisButtons) _mergedButtons.Add(b);
                    foreach (var b in _xnaButtons) _mergedButtons.Add(b);
                }
                if (_captureCallback != null)
                {
                    if (_pendingCapturedButton < 0)
                    {
                        foreach (var b in _mergedButtons)
                            if (!_prevMergedButtons.Contains(b)) { _pendingCapturedButton = b; break; }
                    }
                    if (_pendingCapturedButton >= 0)
                    {
                        capturedCode = _pendingCapturedButton;
                        _pendingCapturedButton = -1;
                        captureCb = _captureCallback;
                        _captureCallback = null;
                    }
                }
                Array.Clear(_gamepadLaneDown, 0, _gamepadLaneDown.Length);
                if (GamepadEnabledBindable.Value && _inGameplay && !_isPaused)
                {
                    var binds = GetBindingsArrayLocked(_activeKeyCount);
                    for (var i = 0; i < binds.Length && i < MaxLanes; i++)
                        if (binds[i] > 0 && _mergedButtons.Contains(binds[i])) _gamepadLaneDown[i] = true;
                    if ((_mergedButtons.Contains(108) && !_prevMergedButtons.Contains(108)) ||
                        (_mergedButtons.Contains(109) && !_prevMergedButtons.Contains(109)))
                        _gamepadPauseJustPressed = true;
                }
            }
            captureCb?.Invoke(capturedCode);
        }

        public bool IsGameplayLaneDown(int lane)
        {
            if ((uint)lane >= MaxLanes) return false;
            lock (_lock)
                return _inGameplay && !_isPaused &&
                    ((TouchEnabledBindable.Value && _touchLaneDown[lane]) ||
                     (GamepadEnabledBindable.Value && _gamepadLaneDown[lane]));
        }

        public bool IsTouchLaneDown(int lane)
        {
            if ((uint)lane >= MaxLanes) return false;
            lock (_lock) return _inGameplay && !_isPaused && TouchEnabledBindable.Value && _touchLaneDown[lane];
        }

        public bool ConsumeGameplayPauseJustPressed()
        {
            lock (_lock)
            {
                var fired = _touchPauseJustPressed || _gamepadPauseJustPressed;
                _touchPauseJustPressed = false;
                _gamepadPauseJustPressed = false;
                return fired;
            }
        }

        public RectangleF GetTouchLaneRect(int lane)
        {
            lock (_lock)
            {
                RecomputeTouchLayout();
                return (uint)lane < MaxLanes ? _touchLaneRects[lane] : RectangleF.Empty;
            }
        }

        public void OnGameplayJudgement(Judgement judgement, bool wasTouchHit)
        {
            if (!OperatingSystem.IsAndroid() || judgement == Judgement.Ghost) return;
            var allow = wasTouchHit ? TouchVibrationEnabledBindable.Value : GamepadVibrationEnabledBindable.Value;
            if (!allow || !AndroidPlatformBridge.HasVibrator) return;
            var now = Environment.TickCount64;
            if (now - _lastVibrateTick < 16) return;
            _lastVibrateTick = now;
            var intensity = GamepadVibrationIntensityBindable.Value / 100f;
            var ms = judgement == Judgement.Miss ? 22 : 11;
            var amp = judgement == Judgement.Miss ? 220 : 135;
            AndroidPlatformBridge.Vibrate(ms, Math.Clamp((int)(amp * intensity), 15, 255));
        }

        public string[] GetGamepad4KPresetNames() => Preset4KNames;

        public int GetCurrent4KPresetIndex()
        {
            lock (_lock)
            {
                var cur = GetBindingsArrayLocked(4);
                for (var p = 0; p < Preset4KButtons.Length; p++)
                {
                    var match = true;
                    for (var i = 0; i < 4; i++)
                        if (cur[i] != Preset4KButtons[p][i]) { match = false; break; }
                    if (match) return p;
                }
                return 0;
            }
        }

        public void Apply4KPreset(int index)
        {
            if ((uint)index >= Preset4KButtons.Length) return;
            lock (_lock) _bindings[4] = (int[])Preset4KButtons[index].Clone();
            SaveConfig();
        }

        public int GetGamepadBindingForLane(int keyCount, int lane)
        {
            lock (_lock)
            {
                var arr = GetBindingsArrayLocked(keyCount);
                return (uint)lane < arr.Length ? arr[lane] : 0;
            }
        }

        public void SetGamepadBindingForLane(int keyCount, int lane, int button)
        {
            lock (_lock)
            {
                var arr = GetBindingsArrayLocked(keyCount);
                if ((uint)lane < arr.Length) arr[lane] = button;
            }
            SaveConfig();
        }

        public void BeginButtonCapture(Action<int> onCaptured)
        {
            lock (_lock) { _pendingCapturedButton = -1; _captureCallback = onCaptured; }
        }

        public void CancelButtonCapture()
        {
            lock (_lock) { _captureCallback = null; _pendingCapturedButton = -1; }
        }

        public void ResetAllToDefaults()
        {
            _suppressSave = true;
            try
            {
                TouchEnabledBindable.Value = true;
                TouchHeightPercentBindable.Value = 32;
                TouchMarginBottomBindable.Value = 12;
                TouchSpacingBindable.Value = 8;
                TouchOpacityPercentBindable.Value = 45;
                TouchEdgeGuardBindable.Value = true;
                TouchShowLabelsBindable.Value = true;
                TouchVibrationEnabledBindable.Value = true;
                GamepadEnabledBindable.Value = true;
                GamepadDeadzoneBindable.Value = 22;
                GamepadVibrationEnabledBindable.Value = true;
                GamepadVibrationIntensityBindable.Value = 65;
                lock (_lock) ResetBindingsDictionary();
            }
            finally { _suppressSave = false; }
            RecomputeTouchLayout();
            SaveConfig();
        }

        public static string FormatButtonLabel(int button) => button switch
        {
            19 => "D-Pad Up", 20 => "D-Pad Down", 21 => "D-Pad Left", 22 => "D-Pad Right", 23 => "D-Pad Center",
            96 => "Button A", 97 => "Button B", 98 => "Button C", 99 => "Button X", 100 => "Button Y", 101 => "Button Z",
            102 => "L1 / LB", 103 => "R1 / RB", 104 => "L2 / LT", 105 => "R2 / RT", 106 => "L3", 107 => "R3",
            108 => "Start", 109 => "Select", 110 => "Mode",
            StickLeft => "L-Stick Left", StickRight => "L-Stick Right", StickUp => "L-Stick Up", StickDown => "L-Stick Down",
            <= 0 => "Unbound",
            _ => $"Key {button}"
        };

        private void OnTouchSnapshotUpdated()
        {
            var touches = AndroidPlatformBridge.CurrentTouchSnapshot;
            lock (_lock)
            {
                Array.Clear(_touchLaneDown, 0, _touchLaneDown.Length);
                if (!_inGameplay || _isPaused || !TouchEnabledBindable.Value || touches == null || touches.Length == 0)
                    return;
                RecomputeTouchLayout();
                var kc = Math.Clamp(_activeKeyCount, 1, MaxLanes);
                var gd = GameBase.Game?.GraphicsDevice;
                var scale = WindowManager.ScreenScale;
                var sx = scale.X > 0.001f ? scale.X : 1f;
                var sy = scale.Y > 0.001f ? scale.Y : 1f;
                for (var i = 0; i < touches.Length; i++)
                {
                    var t = touches[i];
                    if (t.State == TouchLocationState.Invalid || t.State == TouchLocationState.Released) continue;
                    var px = t.Position.X;
                    var py = t.Position.Y;
                    if (gd != null && TouchPanel.DisplayWidth > 0 && TouchPanel.DisplayHeight > 0)
                    {
                        px = px * gd.PresentationParameters.BackBufferWidth / TouchPanel.DisplayWidth;
                        py = py * gd.PresentationParameters.BackBufferHeight / TouchPanel.DisplayHeight;
                    }
                    var vx = px / sx;
                    var vy = py / sy;
                    if (t.State == TouchLocationState.Pressed && TouchPauseRect.Contains(new Vector2(vx, vy)))
                    {
                        _touchPauseJustPressed = true;
                        continue;
                    }
                    if (vy < _zoneTopY || vy > _zoneBottomY || vx < _zoneLeftX - 18f || vx > _zoneRightX + 18f) continue;
                    var bestLane = -1;
                    var bestDist = float.MaxValue;
                    for (var l = 0; l < kc; l++)
                    {
                        var r = _touchLaneRects[l];
                        var dist = Math.Abs(vx - (r.X + r.Width * 0.5f));
                        if (dist < bestDist) { bestDist = dist; bestLane = l; }
                    }
                    if (bestLane >= 0) _touchLaneDown[bestLane] = true;
                }
            }
        }

        private void OnNativeGamepadButton(int keyCode, bool isDown)
        {
            lock (_lock)
            {
                if (isDown)
                {
                    if (_nativeButtons.Add(keyCode) && _captureCallback != null && _pendingCapturedButton < 0)
                        _pendingCapturedButton = keyCode;
                }
                else _nativeButtons.Remove(keyCode);
            }
        }

        private void OnNativeGamepadAxes(float lx, float ly, float hx, float hy, float lt, float rt)
        {
            var dz = Math.Clamp(GamepadDeadzoneBindable.Value / 100f, 0.05f, 0.85f);
            lock (_lock)
            {
                SetAxisCodeLocked(21, hx < -0.5f); SetAxisCodeLocked(22, hx > 0.5f);
                SetAxisCodeLocked(19, hy < -0.5f); SetAxisCodeLocked(20, hy > 0.5f);
                SetAxisCodeLocked(104, lt > 0.35f); SetAxisCodeLocked(105, rt > 0.35f);
                SetAxisCodeLocked(StickLeft, lx < -dz); SetAxisCodeLocked(StickRight, lx > dz);
                SetAxisCodeLocked(StickUp, ly < -dz); SetAxisCodeLocked(StickDown, ly > dz);
            }
        }

        private void SetAxisCodeLocked(int code, bool down)
        {
            if (down)
            {
                if (_axisButtons.Add(code) && _captureCallback != null && _pendingCapturedButton < 0)
                    _pendingCapturedButton = code;
            }
            else _axisButtons.Remove(code);
        }

        private void PollXnaGamepadLocked()
        {
            _xnaButtons.Clear();
            if (!GamepadEnabledBindable.Value) return;
            try
            {
                var st = GamePad.GetState(PlayerIndex.One);
                if (!st.IsConnected) return;
                if (st.DPad.Up == ButtonState.Pressed) _xnaButtons.Add(19);
                if (st.DPad.Down == ButtonState.Pressed) _xnaButtons.Add(20);
                if (st.DPad.Left == ButtonState.Pressed) _xnaButtons.Add(21);
                if (st.DPad.Right == ButtonState.Pressed) _xnaButtons.Add(22);
                if (st.Buttons.A == ButtonState.Pressed) _xnaButtons.Add(96);
                if (st.Buttons.B == ButtonState.Pressed) _xnaButtons.Add(97);
                if (st.Buttons.X == ButtonState.Pressed) _xnaButtons.Add(99);
                if (st.Buttons.Y == ButtonState.Pressed) _xnaButtons.Add(100);
                if (st.Buttons.LeftShoulder == ButtonState.Pressed) _xnaButtons.Add(102);
                if (st.Buttons.RightShoulder == ButtonState.Pressed) _xnaButtons.Add(103);
                if (st.Triggers.Left > 0.35f) _xnaButtons.Add(104);
                if (st.Triggers.Right > 0.35f) _xnaButtons.Add(105);
                if (st.Buttons.LeftStick == ButtonState.Pressed) _xnaButtons.Add(106);
                if (st.Buttons.RightStick == ButtonState.Pressed) _xnaButtons.Add(107);
                if (st.Buttons.Start == ButtonState.Pressed) _xnaButtons.Add(108);
                if (st.Buttons.Back == ButtonState.Pressed) _xnaButtons.Add(109);
                var dz = Math.Clamp(GamepadDeadzoneBindable.Value / 100f, 0.05f, 0.85f);
                var ls = st.ThumbSticks.Left;
                if (ls.X < -dz) _xnaButtons.Add(StickLeft);
                if (ls.X > dz) _xnaButtons.Add(StickRight);
                if (ls.Y > dz) _xnaButtons.Add(StickUp);
                if (ls.Y < -dz) _xnaButtons.Add(StickDown);
            }
            catch { }
        }

        private Keys[] GetMenuNavVirtualKeys()
        {
            if (!GamepadEnabledBindable.Value) return Array.Empty<Keys>();
            lock (_lock)
            {
                if (_captureCallback != null || (_inGameplay && !_isPaused) || _mergedButtons.Count == 0)
                    return Array.Empty<Keys>();
                var keys = new List<Keys>(8);
                if (_mergedButtons.Contains(19) || _mergedButtons.Contains(StickUp)) keys.Add(Keys.Up);
                if (_mergedButtons.Contains(20) || _mergedButtons.Contains(StickDown)) keys.Add(Keys.Down);
                if (_mergedButtons.Contains(21) || _mergedButtons.Contains(StickLeft)) keys.Add(Keys.Left);
                if (_mergedButtons.Contains(22) || _mergedButtons.Contains(StickRight)) keys.Add(Keys.Right);
                if (_mergedButtons.Contains(96) || _mergedButtons.Contains(23)) keys.Add(Keys.Enter);
                if (_mergedButtons.Contains(97)) keys.Add(Keys.Escape);
                if (_mergedButtons.Contains(102)) keys.Add(Keys.PageUp);
                if (_mergedButtons.Contains(103)) keys.Add(Keys.PageDown);
                return keys.Count > 0 ? keys.ToArray() : Array.Empty<Keys>();
            }
        }

        private void RecomputeTouchLayout()
        {
            var vw = Math.Max(640f, WindowManager.Width);
            var vh = Math.Max(360f, WindowManager.Height);
            var eg = TouchEdgeGuardBindable.Value;
            var safeL = eg ? Math.Max(0f, AndroidPlatformBridge.SafeInsetLeft) * vw : 0f;
            var safeR = eg ? Math.Max(0f, AndroidPlatformBridge.SafeInsetRight) * vw : 0f;
            var safeT = eg ? Math.Max(0f, AndroidPlatformBridge.SafeInsetTop) * vh : 0f;
            var safeB = eg ? Math.Max(0f, AndroidPlatformBridge.SafeInsetBottom) * vh : 0f;
            var sidePad = eg ? 28f : 12f;
            _zoneLeftX = safeL + sidePad;
            _zoneRightX = Math.Max(_zoneLeftX + 200f, vw - safeR - sidePad);
            var zoneH = Math.Clamp(vh * (TouchHeightPercentBindable.Value / 100f), 110f, vh * 0.65f);
            _zoneBottomY = vh - safeB - TouchMarginBottomBindable.Value;
            _zoneTopY = Math.Max(safeT + 90f, _zoneBottomY - zoneH);
            var kc = Math.Clamp(_activeKeyCount, 1, MaxLanes);
            var spacing = Math.Max(0f, TouchSpacingBindable.Value);
            var laneW = Math.Max(32f, (_zoneRightX - _zoneLeftX - spacing * (kc - 1)) / kc);
            for (var i = 0; i < MaxLanes; i++)
                _touchLaneRects[i] = i < kc
                    ? new RectangleF(_zoneLeftX + i * (laneW + spacing), _zoneTopY, laneW, _zoneBottomY - _zoneTopY)
                    : RectangleF.Empty;
            TouchPauseRect = new RectangleF(vw - safeR - 92f, safeT + 14f, 76f, 64f);
        }

        private void ResetBindingsDictionary()
        {
            _bindings.Clear();
            for (var k = 1; k <= MaxLanes; k++)
            {
                if (k == 4) { _bindings[4] = (int[])Preset4KButtons[0].Clone(); continue; }
                var arr = new int[k];
                for (var i = 0; i < k; i++) arr[i] = GenericDefaults[i % GenericDefaults.Length];
                _bindings[k] = arr;
            }
        }

        private int[] GetBindingsArrayLocked(int keyCount)
        {
            var kc = Math.Clamp(keyCount, 1, MaxLanes);
            if (!_bindings.TryGetValue(kc, out var arr) || arr == null || arr.Length != kc)
            {
                arr = new int[kc];
                for (var i = 0; i < kc; i++)
                    arr[i] = kc == 4 ? Preset4KButtons[0][i] : GenericDefaults[i % GenericDefaults.Length];
                _bindings[kc] = arr;
            }
            return arr;
        }

        private void HookBindables()
        {
            TouchEnabledBindable.ValueChanged += (_, __) => { AndroidPlatformBridge.SuppressMouseFromTouch = OperatingSystem.IsAndroid() && _inGameplay && !_isPaused && TouchEnabledBindable.Value; SaveConfig(); };
            TouchHeightPercentBindable.ValueChanged += (_, __) => { RecomputeTouchLayout(); SaveConfig(); };
            TouchMarginBottomBindable.ValueChanged += (_, __) => { RecomputeTouchLayout(); SaveConfig(); };
            TouchSpacingBindable.ValueChanged += (_, __) => { RecomputeTouchLayout(); SaveConfig(); };
            TouchOpacityPercentBindable.ValueChanged += (_, __) => SaveConfig();
            TouchEdgeGuardBindable.ValueChanged += (_, __) => { RecomputeTouchLayout(); SaveConfig(); };
            TouchShowLabelsBindable.ValueChanged += (_, __) => SaveConfig();
            TouchVibrationEnabledBindable.ValueChanged += (_, __) => SaveConfig();
            GamepadEnabledBindable.ValueChanged += (_, __) => SaveConfig();
            GamepadDeadzoneBindable.ValueChanged += (_, __) => SaveConfig();
            GamepadVibrationEnabledBindable.ValueChanged += (_, __) => SaveConfig();
            GamepadVibrationIntensityBindable.ValueChanged += (_, __) => SaveConfig();
        }

        private static string GetConfigPath() => Path.Combine(
            string.IsNullOrWhiteSpace(WobbleGame.WorkingDirectory) ? AppContext.BaseDirectory : WobbleGame.WorkingDirectory,
            "android_controls.json");

        private void LoadConfig()
        {
            _suppressSave = true;
            try
            {
                var path = GetConfigPath();
                if (!File.Exists(path)) return;
                var cfg = JsonConvert.DeserializeObject<SavedConfig>(File.ReadAllText(path));
                if (cfg == null) return;
                TouchEnabledBindable.Value = cfg.TouchEnabled;
                TouchHeightPercentBindable.Value = cfg.TouchHeightPercent;
                TouchMarginBottomBindable.Value = cfg.TouchMarginBottom;
                TouchSpacingBindable.Value = cfg.TouchSpacing;
                TouchOpacityPercentBindable.Value = cfg.TouchOpacityPercent;
                TouchEdgeGuardBindable.Value = cfg.TouchEdgeGuard;
                TouchShowLabelsBindable.Value = cfg.TouchShowLabels;
                TouchVibrationEnabledBindable.Value = cfg.TouchVibrationEnabled;
                GamepadEnabledBindable.Value = cfg.GamepadEnabled;
                GamepadDeadzoneBindable.Value = cfg.GamepadDeadzone;
                GamepadVibrationEnabledBindable.Value = cfg.GamepadVibrationEnabled;
                GamepadVibrationIntensityBindable.Value = cfg.GamepadVibrationIntensity;
                if (cfg.GamepadBindings != null)
                    lock (_lock)
                        foreach (var kv in cfg.GamepadBindings)
                            if (kv.Key >= 1 && kv.Key <= MaxLanes && kv.Value != null && kv.Value.Length == kv.Key)
                                _bindings[kv.Key] = (int[])kv.Value.Clone();
            }
            catch { }
            finally { _suppressSave = false; }
        }

        private void SaveConfig()
        {
            if (_suppressSave) return;
            try
            {
                SavedConfig cfg;
                lock (_lock)
                {
                    var map = new Dictionary<int, int[]>();
                    foreach (var kv in _bindings) map[kv.Key] = (int[])kv.Value.Clone();
                    cfg = new SavedConfig
                    {
                        TouchEnabled = TouchEnabledBindable.Value,
                        TouchHeightPercent = TouchHeightPercentBindable.Value,
                        TouchMarginBottom = TouchMarginBottomBindable.Value,
                        TouchSpacing = TouchSpacingBindable.Value,
                        TouchOpacityPercent = TouchOpacityPercentBindable.Value,
                        TouchEdgeGuard = TouchEdgeGuardBindable.Value,
                        TouchShowLabels = TouchShowLabelsBindable.Value,
                        TouchVibrationEnabled = TouchVibrationEnabledBindable.Value,
                        GamepadEnabled = GamepadEnabledBindable.Value,
                        GamepadDeadzone = GamepadDeadzoneBindable.Value,
                        GamepadVibrationEnabled = GamepadVibrationEnabledBindable.Value,
                        GamepadVibrationIntensity = GamepadVibrationIntensityBindable.Value,
                        GamepadBindings = map
                    };
                }
                var path = GetConfigPath();
                Directory.CreateDirectory(Path.GetDirectoryName(path) ?? ".");
                File.WriteAllText(path, JsonConvert.SerializeObject(cfg, Formatting.Indented));
            }
            catch { }
        }
    }
}
""",
    encoding="utf-8",
) 
# 23) TouchPlayfieldOverlay + Hooks en Gameplay (InputManagerKeys, HitObjectManagerKeys, GameplayScreen, GameplayScreenView, QuaverGame)
android_input_dir = root / "Quaver.Shared" / "Input" / "Android"
android_input_dir.mkdir(parents=True, exist_ok=True)
(android_input_dir / "TouchPlayfieldOverlay.cs").write_text(
    """using System;
using Microsoft.Xna.Framework;
using Quaver.Shared.Assets;
using Quaver.Shared.Screens.Gameplay;
using Wobble.Graphics;
using Wobble.Graphics.Sprites;
using Wobble.Graphics.Sprites.Text;
using Wobble.Managers;
using ColorHelper = Quaver.Shared.Helpers.ColorHelper;

namespace Quaver.Shared.Input.Android
{
    public sealed class TouchPlayfieldOverlay : Container
    {
        private readonly GameplayScreen _screen;
        private readonly int _keyCount;
        private readonly Sprite[] _laneBoxes;
        private readonly Sprite[] _laneBars;
        private readonly SpriteTextPlus[] _laneLabels;
        private readonly Sprite _pauseBox;
        private readonly SpriteTextPlus _pauseLabel;

        public TouchPlayfieldOverlay(GameplayScreen screen, int keyCount)
        {
            _screen = screen;
            _keyCount = Math.Clamp(keyCount, 1, 10);
            _laneBoxes = new Sprite[_keyCount];
            _laneBars = new Sprite[_keyCount];
            _laneLabels = new SpriteTextPlus[_keyCount];

            AndroidControlsManager.Instance.SetGameplayContext(true, screen.IsPaused, _keyCount);

            for (var i = 0; i < _keyCount; i++)
            {
                var box = new Sprite
                {
                    Parent = this,
                    Image = UserInterface.BlankBox,
                    Tint = ColorHelper.HexToColor("#111722"),
                    UsePreviousSpriteBatchOptions = true
                };
                box.AddBorder(ColorHelper.HexToColor("#45D6F5"), 2);

                var bar = new Sprite
                {
                    Parent = box,
                    Image = UserInterface.BlankBox,
                    Alignment = Alignment.BotCenter,
                    Tint = ColorHelper.HexToColor("#45D6F5"),
                    UsePreviousSpriteBatchOptions = true
                };

                var lbl = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), $"{i + 1}", 26)
                {
                    Parent = box,
                    Alignment = Alignment.MidCenter,
                    Tint = Color.White,
                    UsePreviousSpriteBatchOptions = true
                };

                _laneBoxes[i] = box;
                _laneBars[i] = bar;
                _laneLabels[i] = lbl;
            }

            _pauseBox = new Sprite
            {
                Parent = this,
                Image = UserInterface.BlankBox,
                Tint = ColorHelper.HexToColor("#141923"),
                UsePreviousSpriteBatchOptions = true
            };
            _pauseBox.AddBorder(ColorHelper.HexToColor("#45D6F5"), 2);

            _pauseLabel = new SpriteTextPlus(FontManager.GetWobbleFont(Fonts.InterSemiBold), "II", 22)
            {
                Parent = _pauseBox,
                Alignment = Alignment.MidCenter,
                Tint = Color.White,
                UsePreviousSpriteBatchOptions = true
            };
        }

        public override void Update(GameTime gameTime)
        {
            base.Update(gameTime);

            var ctrl = AndroidControlsManager.Instance;
            var show = OperatingSystem.IsAndroid()
                && ctrl.TouchEnabledBindable.Value
                && !_screen.IsPaused
                && !_screen.Failed
                && !_screen.IsPlayComplete;

            var baseAlpha = Math.Clamp(ctrl.TouchOpacityPercentBindable.Value / 100f, 0.10f, 0.95f);

            for (var i = 0; i < _keyCount; i++)
            {
                var box = _laneBoxes[i];
                box.Visible = show;
                if (!show) continue;

                var rect = ctrl.GetTouchLaneRect(i);
                var pressed = ctrl.IsGameplayLaneDown(i);

                box.X = rect.X;
                box.Y = rect.Y;
                box.Width = rect.Width;
                box.Height = rect.Height;
                box.Tint = pressed ? ColorHelper.HexToColor("#257EA8") : ColorHelper.HexToColor("#0E141E");
                box.Alpha = pressed ? Math.Min(0.88f, baseAlpha + 0.35f) : baseAlpha * 0.65f;
                box.Border.Alpha = pressed ? 0.95f : Math.Min(0.85f, baseAlpha + 0.15f);

                _laneBars[i].Width = Math.Max(8f, rect.Width - 12f);
                _laneBars[i].Height = pressed ? 10f : 5f;
                _laneBars[i].Y = -6f;
                _laneBars[i].Alpha = pressed ? 1f : Math.Min(0.85f, baseAlpha + 0.25f);

                _laneLabels[i].Visible = ctrl.TouchShowLabelsBindable.Value;
                _laneLabels[i].Alpha = pressed ? 1f : Math.Clamp(baseAlpha + 0.2f, 0.25f, 0.9f);
            }

            _pauseBox.Visible = show && _screen.SpectatorClient == null;
            if (_pauseBox.Visible)
            {
                var pr = ctrl.TouchPauseRect;
                _pauseBox.X = pr.X;
                _pauseBox.Y = pr.Y;
                _pauseBox.Width = pr.Width;
                _pauseBox.Height = pr.Height;
                _pauseBox.Alpha = Math.Clamp(baseAlpha + 0.25f, 0.45f, 0.92f);
                _pauseBox.Border.Alpha = 0.85f;
                _pauseLabel.Alpha = 0.95f;
            }
        }
    }
}
""",
    encoding="utf-8",
)

imk_cs = root / "Quaver.Shared" / "Screens" / "Gameplay" / "Rulesets" / "Input" / "InputManagerKeys.cs"
if imk_cs.is_file():
    imkt = imk_cs.read_text(encoding="utf-8-sig")
    if "AndroidControlsManager" not in imkt:
        imkt = imkt.replace(
            "using Quaver.Shared.Input.Global;",
            "using Quaver.Shared.Input.Global;\nusing Quaver.Shared.Input.Android;",
            1,
        )
        old_imk_loop = """                // A key was uniquely pressed.
                if (!BindingStore[lane].Pressed && (GenericKeyManager.IsUniquePress(BindingStore[lane].Key.Value) &&
                                                    !Ruleset.Screen.InReplayMode || Ruleset.Screen.InReplayMode && ReplayInputManager.UniquePresses[lane]))
                {
                    // Update Replay Manager. Reset UniquePresses value for this lane.
                    if (Ruleset.Screen.InReplayMode)
                        ReplayInputManager.UniquePresses[inputLane] = false;

                    // Toggle this key on from BindingStore and enable needsUpdating value to handle key press
                    BindingStore[lane].Pressed = true;
                    needsUpdating = true;

                    var screenView = (GameplayScreenView)Ruleset.Screen.View;
                    screenView.KpsDisplay.AddClick();
                }
                // A key was uniquely released.
                else if (BindingStore[lane].Pressed && (GenericKeyManager.IsUniqueRelease(BindingStore[lane].Key.Value) &&
                                                        !Ruleset.Screen.InReplayMode
                                                    || Ruleset.Screen.InReplayMode && ReplayInputManager.UniqueReleases[lane]))"""
        new_imk_loop = """                var androidLaneDown = !Ruleset.Screen.InReplayMode && AndroidControlsManager.Instance.IsGameplayLaneDown(inputLane);

                // A key was uniquely pressed.
                if (!BindingStore[lane].Pressed && ((GenericKeyManager.IsUniquePress(BindingStore[lane].Key.Value) || androidLaneDown) &&
                                                    !Ruleset.Screen.InReplayMode || Ruleset.Screen.InReplayMode && ReplayInputManager.UniquePresses[lane]))
                {
                    // Update Replay Manager. Reset UniquePresses value for this lane.
                    if (Ruleset.Screen.InReplayMode)
                        ReplayInputManager.UniquePresses[inputLane] = false;

                    // Toggle this key on from BindingStore and enable needsUpdating value to handle key press
                    BindingStore[lane].Pressed = true;
                    needsUpdating = true;

                    var screenView = (GameplayScreenView)Ruleset.Screen.View;
                    screenView.KpsDisplay.AddClick();
                }
                // A key was uniquely released.
                else if (BindingStore[lane].Pressed && (!GenericKeyManager.IsDown(BindingStore[lane].Key.Value) && !androidLaneDown &&
                                                        !Ruleset.Screen.InReplayMode
                                                    || Ruleset.Screen.InReplayMode && ReplayInputManager.UniqueReleases[lane]))"""
        assert old_imk_loop in imkt, "InputManagerKeys loop anchor missing"
        imkt = imkt.replace(old_imk_loop, new_imk_loop, 1)

        old_imk_judg = """            if (ReplayInputManager == null)
            {
                playfield.Stage.ComboDisplay.MakeVisible();"""
        new_imk_judg = """            if (ReplayInputManager == null)
            {
                AndroidControlsManager.Instance.OnGameplayJudgement(judgement, AndroidControlsManager.Instance.IsTouchLaneDown(lane));
                playfield.Stage.ComboDisplay.MakeVisible();"""
        assert old_imk_judg in imkt, "InputManagerKeys judgement anchor missing"
        imkt = imkt.replace(old_imk_judg, new_imk_judg, 1)
        imk_cs.write_text(imkt, encoding="utf-8")

homk_cs = root / "Quaver.Shared" / "Screens" / "Gameplay" / "Rulesets" / "Keys" / "HitObjects" / "HitObjectManagerKeys.cs"
if homk_cs.is_file():
    homkt = homk_cs.read_text(encoding="utf-8-sig")
    if "AndroidControlsManager" not in homkt:
        homkt = homkt.replace(
            "using Quaver.Shared.Screens.Gameplay.Rulesets.Input;",
            "using Quaver.Shared.Screens.Gameplay.Rulesets.Input;\nusing Quaver.Shared.Input.Android;",
            1,
        )
        old_homk_miss = """                    if (im?.ReplayInputManager == null)
                    {
                        playfield.Stage.ComboDisplay.MakeVisible();
                        playfield.Stage.HitBubbles.AddJudgement(Judgement.Miss);"""
        new_homk_miss = """                    if (im?.ReplayInputManager == null)
                    {
                        AndroidControlsManager.Instance.OnGameplayJudgement(Judgement.Miss, false);
                        playfield.Stage.ComboDisplay.MakeVisible();
                        playfield.Stage.HitBubbles.AddJudgement(Judgement.Miss);"""
        assert old_homk_miss in homkt, "HitObjectManagerKeys miss anchor missing"
        homkt = homkt.replace(old_homk_miss, new_homk_miss, 1)
        homk_cs.write_text(homkt, encoding="utf-8")

gs_cs = root / "Quaver.Shared" / "Screens" / "Gameplay" / "GameplayScreen.cs"
if gs_cs.is_file():
    gst = gs_cs.read_text(encoding="utf-8-sig")
    if "AndroidControlsManager" not in gst:
        gst = gst.replace(
            "using Quaver.Shared.Input.Global;",
            "using Quaver.Shared.Input.Global;\nusing Quaver.Shared.Input.Android;",
            1,
        )
        old_gs_upd = """        public override void Update(GameTime gameTime)
        {
            TimeSinceLastJudgementsSentToServer += gameTime.ElapsedGameTime.TotalMilliseconds;"""
        new_gs_upd = """        public override void Update(GameTime gameTime)
        {
            AndroidControlsManager.Instance.SetGameplayContext(!IsSongSelectPreview, IsPaused, ModeHelper.ToKeyCount(Map.Mode, Map.HasScratchKey));
            TimeSinceLastJudgementsSentToServer += gameTime.ElapsedGameTime.TotalMilliseconds;"""
        assert old_gs_upd in gst, "GameplayScreen Update anchor missing"
        gst = gst.replace(old_gs_upd, new_gs_upd, 1)

        old_gs_inp = """            // Handle pausing
            if (!Failed && !IsPlayComplete && !IsSongSelectPreview)
                HandlePauseInput(gameTime);"""
        new_gs_inp = """            if (AndroidControlsManager.Instance.ConsumeGameplayPauseJustPressed() && !IsPaused && !Failed && !IsPlayComplete && !IsSongSelectPreview && SpectatorClient == null && DialogManager.Dialogs.Count == 0 && OnlineManager.CurrentGame == null)
            {
                TimePauseKeyHeld = TimeToHoldPause;
                Pause(gameTime);
                return;
            }

            // Handle pausing
            if (!Failed && !IsPlayComplete && !IsSongSelectPreview)
                HandlePauseInput(gameTime);"""
        assert old_gs_inp in gst, "GameplayScreen HandleInput anchor missing"
        gst = gst.replace(old_gs_inp, new_gs_inp, 1)

        old_gs_des = """        public override void Destroy()
        {
            if (IsCalibratingOffset)"""
        new_gs_des = """        public override void Destroy()
        {
            AndroidControlsManager.Instance.SetGameplayContext(false, false);
            if (IsCalibratingOffset)"""
        assert old_gs_des in gst, "GameplayScreen Destroy anchor missing"
        gst = gst.replace(old_gs_des, new_gs_des, 1)
        gs_cs.write_text(gst, encoding="utf-8")

gsv_cs = root / "Quaver.Shared" / "Screens" / "Gameplay" / "GameplayScreenView.cs"
if gsv_cs.is_file():
    gsvt = gsv_cs.read_text(encoding="utf-8-sig")
    if "TouchPlayfieldOverlay" not in gsvt:
        gsvt = gsvt.replace(
            "using Quaver.Shared.Modifiers;",
            "using Quaver.Shared.Modifiers;\nusing Quaver.Shared.Input.Android;",
            1,
        )
        old_gsv_pause = """            // Create pause screen last.
            if (Screen.SpectatorClient == null)
                PauseScreen = new PauseScreen(Screen) { Parent = Container };"""
        new_gsv_pause = """            if (OperatingSystem.IsAndroid() && !Screen.IsSongSelectPreview && !Screen.InReplayMode)
                new TouchPlayfieldOverlay(Screen, ModeHelper.ToKeyCount(Screen.Map.Mode, Screen.Map.HasScratchKey)) { Parent = Container };

            // Create pause screen last.
            if (Screen.SpectatorClient == null)
                PauseScreen = new PauseScreen(Screen) { Parent = Container };"""
        assert old_gsv_pause in gsvt, "GameplayScreenView pause anchor missing"
        gsvt = gsvt.replace(old_gsv_pause, new_gsv_pause, 1)
        gsv_cs.write_text(gsvt, encoding="utf-8")

qg_cs = root / "Quaver.Shared" / "QuaverGame.cs"
if qg_cs.is_file():
    qgt = qg_cs.read_text(encoding="utf-8-sig")
    if "AndroidControlsManager" not in qgt:
        qgt = qgt.replace(
            "using Quaver.Shared.Discord;",
            "using Quaver.Shared.Discord;\nusing Quaver.Shared.Input.Android;",
            1,
        )
        old_qg_upd = """            base.Update(gameTime);

            if (SteamManager.IsInitialized)"""
        new_qg_upd = """            AndroidControlsManager.Instance.Update(gameTime);

            base.Update(gameTime);

            if (SteamManager.IsInitialized)"""
        assert old_qg_upd in qgt, "QuaverGame Update anchor missing"
        qgt = qgt.replace(old_qg_upd, new_qg_upd, 1)
        qg_cs.write_text(qgt, encoding="utf-8")
