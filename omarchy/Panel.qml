import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

Panel {
  id: root
  moduleName: "tech.curren.signals"
  ipcTarget: moduleName
  manageIpc: false

  property var anchorItem: null
  property var hostWidget: null
  readonly property var barIdentity: hostWidget || root
  readonly property color contentForeground: bar ? bar.foreground : Color.foreground
  readonly property string contentFontFamily: bar ? bar.fontFamily : Style.font.family
  readonly property color mutedForeground: Qt.rgba(contentForeground.r, contentForeground.g, contentForeground.b, 0.62)
  readonly property color sectionFill: Qt.rgba(contentForeground.r, contentForeground.g, contentForeground.b, 0.045)
  readonly property color sectionBorder: Qt.rgba(contentForeground.r, contentForeground.g, contentForeground.b, 0.16)

  property int activeCount: 0
  property var delayedSignals: []
  property var recentResults: []
  property string asOf: ""
  property string feedState: "Loading"
  property string errorMessage: ""
  property double lastSuccessAt: 0
  property bool requestInFlight: false
  property var activeRequest: null
  property int requestGeneration: 0

  readonly property string apiBaseUrl: {
    var candidate = root.settings && root.settings.apiBaseUrl ? String(root.settings.apiBaseUrl).trim() : ""
    if (!candidate) candidate = "https://api.curren.tech"
    while (candidate.length > 0 && candidate.charAt(candidate.length - 1) === "/") candidate = candidate.slice(0, -1)
    return candidate
  }
  readonly property string summaryUrl: root.apiBaseUrl + "/v1/public/summary"

  function openFromHotkey() { root.controller.show(); refreshIfStale() }
  function open() { root.controller.show(); refreshIfStale() }
  function close() { root.controller.hide() }
  function toggle() { root.opened ? root.close() : root.open() }

  function switchPanel(direction) {
    if (root.bar && typeof root.bar.switchPanelFrom === "function") return root.bar.switchPanelFrom(root.barIdentity, direction)
    return false
  }

  function refreshIfStale() {
    if (Date.now() - root.lastSuccessAt > 60000) refreshNow()
  }

  function setFailure(message) {
    root.feedState = root.lastSuccessAt > 0 ? "Stale" : "Offline"
    root.errorMessage = message
  }

  function refreshNow() {
    if (root.requestInFlight) return
    root.requestInFlight = true
    root.errorMessage = ""
    if (root.lastSuccessAt === 0) root.feedState = "Loading"

    var generation = ++root.requestGeneration
    var request = new XMLHttpRequest()
    root.activeRequest = request
    request.onreadystatechange = function() {
      if (request.readyState !== XMLHttpRequest.DONE || generation !== root.requestGeneration) return
      requestTimeout.stop()
      root.activeRequest = null
      root.requestInFlight = false
      var status = Number(request.status) || 0
      if (status < 200 || status >= 300) {
        root.setFailure(status > 0 ? "HTTP " + status : "Network unavailable")
        return
      }

      try {
        var payload = JSON.parse(request.responseText)
        root.activeCount = Math.max(0, Number(payload.active_count || 0))
        root.delayedSignals = Array.isArray(payload.delayed_signals) ? payload.delayed_signals : []
        root.recentResults = Array.isArray(payload.recent_results) ? payload.recent_results : []
        root.asOf = payload.as_of || ""
        root.lastSuccessAt = Date.now()
        root.feedState = "Live"
        root.errorMessage = ""
      } catch (error) {
        root.setFailure("Malformed API response")
      }
    }
    request.open("GET", root.summaryUrl, true)
    request.setRequestHeader("Accept", "application/json")
    requestTimeout.restart()
    request.send()
  }

  function numberText(value) {
    var number = Number(value)
    if (!isFinite(number)) return "—"
    return (number >= 0 ? "+" : "") + number.toFixed(2) + "R"
  }

  function timeText(value) {
    if (!value) return "—"
    var date = new Date(value)
    if (isNaN(date.getTime())) return "—"
    return Qt.formatDateTime(date, "MMM d · hh:mm")
  }

  function sideText(signal) {
    return signal && signal.side ? String(signal.side).toUpperCase() : "—"
  }

  function signalR(signal) {
    if (!signal) return "—"
    if (signal.realized_r !== undefined && signal.realized_r !== null) return numberText(signal.realized_r)
    return numberText(signal.current_r)
  }

  component CurrenText: Text {
    color: root.contentForeground
    font.family: root.contentFontFamily
    font.pixelSize: Style.font.bodySmall
    renderType: Text.NativeRendering
  }

  component MutedText: CurrenText {
    color: root.mutedForeground
    font.pixelSize: Style.font.caption
  }

  component SignalRow: Rectangle {
    id: row
    required property var signal
    width: parent ? parent.width : 0
    height: Style.space(42)
    radius: Style.space(5)
    color: root.sectionFill
    border.color: root.sectionBorder
    border.width: 1

    Row {
      anchors.fill: parent
      anchors.leftMargin: Style.space(7)
      anchors.rightMargin: Style.space(7)
      spacing: Style.space(8)

      Column {
        width: Math.max(Style.space(105), parent.width * 0.38)
        anchors.verticalCenter: parent.verticalCenter
        spacing: 0
        CurrenText { text: row.signal.symbol || "—"; font.bold: true }
        MutedText { text: root.timeText(row.signal.published_at) }
      }

      Column {
        width: Style.space(62)
        anchors.verticalCenter: parent.verticalCenter
        spacing: 0
        CurrenText { text: root.sideText(row.signal); font.bold: true }
        MutedText { text: row.signal.status || "—" }
      }

      Item { width: Math.max(0, parent.width - Style.space(230)); height: 1 }

      CurrenText {
        anchors.verticalCenter: parent.verticalCenter
        text: root.signalR(row.signal)
        font.bold: true
      }
    }
  }

  Timer {
    id: requestTimeout
    interval: 15000
    repeat: false
    onTriggered: {
      if (!root.requestInFlight) return
      root.requestGeneration += 1
      if (root.activeRequest) root.activeRequest.abort()
      root.activeRequest = null
      root.requestInFlight = false
      root.setFailure("Request timed out")
    }
  }

  Timer {
    interval: 60000
    running: true
    repeat: true
    triggeredOnStart: true
    onTriggered: root.refreshNow()
  }

  KeyboardPanel {
    id: panel
    anchorItem: root.anchorItem
    owner: root.barIdentity
    bar: root.bar
    open: root.opened
    centerOnBar: true
    focusTarget: keyCatcher
    contentWidth: panel.fittedContentWidth(Style.space(430))
    contentHeight: panel.fittedContentHeight(contentColumn.implicitHeight, Style.space(560))

    PanelKeyCatcher {
      id: keyCatcher
      anchors.fill: parent
      onCloseRequested: root.close()
      onTabRequested: function(direction) { root.switchPanel(direction) }

      Flickable {
        anchors.fill: parent
        contentWidth: width
        contentHeight: contentColumn.implicitHeight
        clip: true
        boundsBehavior: Flickable.StopAtBounds

        Column {
          id: contentColumn
          width: parent.width
          spacing: Style.space(6)

          Row {
            width: parent.width
            height: Style.space(30)

            Column {
              anchors.verticalCenter: parent.verticalCenter
              CurrenText { text: "Curren"; font.pixelSize: Style.font.heading; font.bold: true }
              MutedText { text: "Verifiable trading intelligence" }
            }

            Item { width: Math.max(0, parent.width - parent.children[0].implicitWidth - parent.children[2].implicitWidth); height: 1 }

            MutedText {
              anchors.verticalCenter: parent.verticalCenter
              text: root.feedState
              color: root.feedState === "Offline" ? Color.urgent : root.mutedForeground
            }
          }

          Rectangle {
            width: parent.width
            height: Style.space(62)
            radius: Style.space(6)
            color: root.sectionFill
            border.color: root.sectionBorder
            border.width: 1

            Row {
              anchors.fill: parent
              anchors.margins: Style.space(8)

              Column {
                anchors.verticalCenter: parent.verticalCenter
                CurrenText { text: String(root.activeCount); font.pixelSize: Style.font.heading; font.bold: true }
                MutedText { text: "VISIBLE ACTIVE"; font.bold: true }
              }

              Item { width: Math.max(0, parent.width - Style.space(180)); height: 1 }

              Column {
                anchors.verticalCenter: parent.verticalCenter
                CurrenText { text: root.feedState === "Live" ? "PUBLIC PROOF" : root.feedState; font.bold: true }
                MutedText { text: root.asOf ? "as of " + root.timeText(root.asOf) : "waiting for API" }
              }
            }
          }

          MutedText {
            width: parent.width
            visible: root.errorMessage !== ""
            text: root.errorMessage + " · Last valid data is retained when available."
            color: root.feedState === "Offline" ? Color.urgent : root.mutedForeground
            wrapMode: Text.WordWrap
          }

          MutedText { text: "DELAYED ACTIVE"; font.bold: true; visible: root.delayedSignals.length > 0 }
          Repeater {
            model: root.delayedSignals.slice(0, 3)
            delegate: SignalRow { signal: modelData }
          }

          MutedText { text: "RECENT RESULTS"; font.bold: true; visible: root.recentResults.length > 0 }
          Repeater {
            model: root.recentResults.slice(0, 5)
            delegate: SignalRow { signal: modelData }
          }

          MutedText {
            width: parent.width
            visible: root.delayedSignals.length === 0 && root.recentResults.length === 0
            text: root.feedState === "Live" ? "No public signal records available." : "Waiting for Curren public feed."
            horizontalAlignment: Text.AlignHCenter
          }

          MutedText {
            width: parent.width
            text: "Public/delayed proof only · no exchange credentials · no trade execution"
            horizontalAlignment: Text.AlignHCenter
          }
        }
      }
    }
  }
}
