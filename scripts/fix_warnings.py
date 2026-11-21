from pathlib import Path
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

# 6) MainActivity: HUD visible desde el primer instante + juego en capa inferior
ma = root / "android-head" / "MainActivity.cs"
if ma.is_file():
    ma.write_text(r"""using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using Android.App;
using Android.Content;
using Android.Content.PM;
using Android.OS;
using Android.Views;
using Android.Widget;
using Microsoft.Xna.Framework;
using Wobble.Logging;

namespace QuaverAndroid
{
    [Activity(Label = "Quaver", Icon = "@drawable/icon", MainLauncher = true, LaunchMode = LaunchMode.SingleInstance,
        ScreenOrientation = ScreenOrientation.SensorLandscape,
        ConfigurationChanges = ConfigChanges.Orientation | ConfigChanges.Keyboard | ConfigChanges.KeyboardHidden | ConfigChanges.ScreenSize)]
    public class MainActivity : AndroidGameActivity
    {
        private string _crashFile;
        private Quaver.Shared.QuaverGame _game;
        private View _gameView;
        private FrameLayout _rootFrame;
        private TextView _statusText;
        private Handler _handler;

        protected override void OnCreate(Bundle bundle)
        {
            base.OnCreate(bundle);
            Window?.AddFlags(WindowManagerFlags.KeepScreenOn | WindowManagerFlags.Fullscreen);
            var dataDir = FilesDir.AbsolutePath;
            Wobble.WobbleGame.WorkingDirectory = dataDir + "/";
            _crashFile = Path.Combine(dataDir, "informe-fallo.txt");
            HookCrashHandlers();

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

            var logsBtn = new Button(this) { Text = "LOGS" };
            logsBtn.SetBackgroundColor(global::Android.Graphics.Color.Argb(210, 180, 30, 30));
            logsBtn.SetTextColor(global::Android.Graphics.Color.White);
            logsBtn.Click += (s, e) => ShowReport(BuildLogText());
            _rootFrame.AddView(logsBtn, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.WrapContent, ViewGroup.LayoutParams.WrapContent,
                GravityFlags.Top | GravityFlags.Right));

            SetContentView(_rootFrame);

            _handler = new Handler(Looper.MainLooper);
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

        private void StartQuaver(string workDir)
        {
            Wobble.WobbleGame.WorkingDirectory = workDir;
            Directory.SetCurrentDirectory(workDir);
            AndroidDiagnostics.Trace("02.Batteries_V2.Init");
            SQLitePCL.Batteries_V2.Init();
            AndroidDiagnostics.Trace("03.ConfigManager.Initialize");
            Wobble.Logging.Logger.Initialize();
            Quaver.Shared.Config.ConfigManager.Initialize();
            Quaver.Shared.Config.StructuredConfigManager.Initialize();
            System.Globalization.CultureInfo.DefaultThreadCurrentCulture = System.Globalization.CultureInfo.InvariantCulture;
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

            AndroidDiagnostics.Trace("06.game.Run()");
            _game.Run();
        }

        private void ScheduleTracePoll()
        {
            _handler?.PostDelayed(() =>
            {
                try
                {
                    var tracePath = Path.Combine(FilesDir.AbsolutePath, "Logs", "boot-trace.log");
                    if (File.Exists(tracePath) && _statusText != null)
                    {
                        var lines = ReadShared(tracePath).TrimEnd().Split('\n');
                        if (lines.Length > 0)
                            _statusText.Text = lines[lines.Length - 1].Trim();
                    }
                }
                catch { }
                ScheduleTracePoll();
            }, 600);
        }

        public override bool DispatchKeyEvent(KeyEvent e)
        {
            if (e != null && e.KeyCode == Keycode.VolumeDown && e.Action == KeyEventActions.Down)
            {
                try { ShowReport(BuildLogText()); }
                catch (Exception ex) { Android.Util.Log.Error("QuaverAndroid", ex.ToString()); }
                return true;
            }
            return base.DispatchKeyEvent(e);
        }

        private void HookCrashHandlers()
        {
            AppDomain.CurrentDomain.UnhandledException += (s, e) => WriteReport(e.ExceptionObject as Exception, "AppDomain");
            Android.Runtime.AndroidEnvironment.UnhandledExceptionRaiser += (s, e) => WriteReport(e.Exception, "Android");
            TaskScheduler.UnobservedTaskException += (s, e) =>
            {
                WriteReport(e.Exception, "UnobservedTask");
                e.SetObserved();
            };
            AndroidDiagnostics.OnFatal += msg =>
            {
                WriteTextReport("TaskHandler/Fatal", msg);
                try
                {
                    RunOnUiThread(() => ShowReport(BuildLogText() + "\n\n=== EXCEPCION ===\n" + msg));
                }
                catch { }
            };
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
