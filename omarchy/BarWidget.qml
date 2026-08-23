import QtQuick
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui

BarWidget {
  id: root
  moduleName: "tech.curren.signals"

  readonly property int activeCount: panelLoader.item ? panelLoader.item.activeCount : 0
  readonly property string feedState: panelLoader.item ? panelLoader.item.feedState : "Loading"
  readonly property bool opened: panelLoader.item ? panelLoader.item.opened === true : false
  readonly property bool popoutSwitchClosing: panelLoader.item ? panelLoader.item.popoutSwitchClosing === true : false
  readonly property real openPanelIndicatorWidth: button.width
  readonly property real openPanelIndicatorHeight: Math.max(Style.space(10), Math.round(Style.bar.iconSlot * 0.55))

  function injectPanel() {
    var target = panelLoader.item
    if (!target) return
    if ("bar" in target) target.bar = root.bar
    if ("settings" in target) target.settings = root.settings
    if ("anchorItem" in target) target.anchorItem = button
    if ("hostWidget" in target) target.hostWidget = root
  }

  function open() { if (panelLoader.item) panelLoader.item.openFromHotkey() }
  function close() { if (panelLoader.item) panelLoader.item.close() }
  function togglePanel() { if (panelLoader.item) panelLoader.item.toggle() }
  function refresh() { if (panelLoader.item) panelLoader.item.refreshNow() }

  function labelText() {
    if (root.feedState === "Offline") return "CURREN · OFFLINE"
    if (root.feedState === "Stale") return "CURREN · " + root.activeCount + " · STALE"
    if (root.feedState === "Loading") return "CURREN · …"
    return "CURREN · " + root.activeCount + " ACTIVE"
  }

  implicitWidth: button.implicitWidth
  implicitHeight: button.implicitHeight

  onBarChanged: injectPanel()
  onSettingsChanged: injectPanel()

  Loader {
    id: panelLoader
    active: true
    source: Qt.resolvedUrl("Panel.qml")
    visible: false
    onLoaded: {
      root.injectPanel()
      Qt.callLater(root.injectPanel)
    }
  }

  IpcHandler {
    target: root.moduleName
    function refresh(): void { root.refresh() }
    function state(): string {
      return JSON.stringify({ active: root.activeCount, state: root.feedState, opened: root.opened })
    }
    function open(): void { root.open() }
    function close(): void { root.close() }
    function toggle(): void { root.togglePanel() }
  }

  WidgetButton {
    id: button
    anchors.fill: parent
    bar: root.bar
    text: ""
    labelVisible: false
    hasVisualContent: true
    fixedWidth: label.implicitWidth + Style.space(18)
    tooltipText: "Curren Signals · " + root.feedState

    onPressed: function(mouseButton) {
      if (mouseButton === Qt.LeftButton) root.togglePanel()
    }

    Text {
      id: label
      anchors.centerIn: parent
      text: root.labelText()
      color: root.feedState === "Offline" ? Color.urgent : button.foreground
      opacity: root.feedState === "Stale" ? 0.72 : 1.0
      font.family: button.fontFamily
      font.pixelSize: Style.font.bodySmall
      font.bold: true
      renderType: Text.NativeRendering
    }
  }
}
