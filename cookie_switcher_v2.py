from burp import IBurpExtender, ITab, IContextMenuFactory
from javax.swing import (JPanel, JLabel, JTextField, JButton, JMenuItem,
                          JCheckBox, BoxLayout, BorderFactory, Box, SwingConstants)
from java.awt import GridLayout, KeyboardFocusManager, Toolkit, AWTEvent, Font, Color, Dimension, BorderLayout
from java.awt.event import KeyEvent, InputEvent, AWTEventListener
from javax.swing.text import JTextComponent
from java.util import ArrayList


class BurpExtender(IBurpExtender, ITab, IContextMenuFactory, AWTEventListener):

    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("Cookie Switcher v2")

        def load(key):
            v = callbacks.loadExtensionSetting(key)
            return v if v else ""

        self.adminBearer = load("admin_bearer")
        self.adminCookie = load("admin_cookie")
        self.adminCsrf = load("admin_csrf")

        self.userBearer = load("user_bearer")
        self.userCookie = load("user_cookie")
        self.userCsrf = load("user_csrf")

        self.csrfHeaderName = load("csrf_header_name") or "X-CSRF-Token"

        self.chkBearer = JCheckBox("Update Authorization: Bearer", load("chk_bearer") != "0")
        self.chkCookie = JCheckBox("Update Cookie header", load("chk_cookie") != "0")
        self.chkCsrf = JCheckBox("Update CSRF header", load("chk_csrf") == "1")

        # ---------- main panel ----------
        self._panel = JPanel()
        self._panel.setLayout(BoxLayout(self._panel, BoxLayout.Y_AXIS))
        self._panel.setBorder(BorderFactory.createEmptyBorder(15, 20, 15, 20))
        title = JLabel("Cookie Switcher")
        title.setFont(Font("SansSerif", Font.BOLD, 20))
        title.setAlignmentX(0)
        subtitle = JLabel("Swap Authorization / Cookie / CSRF between two profiles")
        subtitle.setFont(Font("SansSerif", Font.PLAIN, 12))
        subtitle.setAlignmentX(0)
        hint = JLabel("Hotkeys (in raw request editor):  Ctrl+Alt+A = Admin    Ctrl+Alt+U = User")
        hint.setFont(Font("SansSerif", Font.ITALIC, 11))
        hint.setAlignmentX(0)

        self._panel.add(title)
        self._panel.add(subtitle)
        self._panel.add(Box.createVerticalStrut(4))
        self._panel.add(hint)
        self._panel.add(Box.createVerticalStrut(12))

        optionsBox = self._buildOptionsBox()
        optionsBox.setAlignmentX(0)
        self._panel.add(optionsBox)
        self._panel.add(Box.createVerticalStrut(10))

        adminBox = self._buildProfileBox("Admin Profile", "admin")
        adminBox.setAlignmentX(0)
        self._panel.add(adminBox)
        self._panel.add(Box.createVerticalStrut(10))

        userBox = self._buildProfileBox("User Profile", "user")
        userBox.setAlignmentX(0)
        self._panel.add(userBox)
        self._panel.add(Box.createVerticalStrut(15))

        saveBtn = JButton("Save Settings", actionPerformed=self.saveSettings)
        saveBtn.setAlignmentX(0)
        saveBtn.setFont(Font("SansSerif", Font.BOLD, 13))
        saveBtn.setMaximumSize(Dimension(160, 32))
        self._panel.add(saveBtn)

        callbacks.addSuiteTab(self)
        callbacks.registerContextMenuFactory(self)

        # Global hotkeys: Ctrl+Alt+A = Admin, Ctrl+Alt+U = User
        Toolkit.getDefaultToolkit().addAWTEventListener(self, AWTEvent.KEY_EVENT_MASK)

    def eventDispatched(self, event):
        if event.getID() != KeyEvent.KEY_PRESSED:
            return
        mods = event.getModifiersEx()
        ctrlAlt = (mods & InputEvent.CTRL_DOWN_MASK) != 0 and (mods & InputEvent.ALT_DOWN_MASK) != 0
        if not ctrlAlt:
            return

        prefix = None
        if event.getKeyCode() == KeyEvent.VK_A:
            prefix = "admin"
        elif event.getKeyCode() == KeyEvent.VK_U:
            prefix = "user"
        if prefix is None:
            return

        focusOwner = KeyboardFocusManager.getCurrentKeyboardFocusManager().getFocusOwner()
        if not isinstance(focusOwner, JTextComponent):
            return

        rawText = focusOwner.getText()
        if not rawText:
            return

        newText = self.applyProfileToRawText(rawText, prefix)
        if newText is not None:
            focusOwner.setText(newText)
            event.consume()

    # ---------- UI builders ----------

    def _titledBox(self, title):
        box = JPanel(GridLayout(0, 2, 6, 6))
        box.setBorder(BorderFactory.createCompoundBorder(
            BorderFactory.createTitledBorder(title),
            BorderFactory.createEmptyBorder(6, 8, 8, 8)
        ))
        return box

    def _buildOptionsBox(self):
        box = self._titledBox("Which components to swap")
        box.setLayout(GridLayout(0, 1, 3, 3))
        box.add(self.chkBearer)
        box.add(self.chkCookie)
        box.add(self.chkCsrf)
        row = JPanel(GridLayout(1, 2, 3, 3))
        row.add(JLabel("CSRF Header Name:"))
        self.csrfHeaderField = JTextField(self.csrfHeaderName, 20)
        row.add(self.csrfHeaderField)
        box.add(row)
        return box

    def _buildProfileBox(self, title, prefix):
        box = self._titledBox(title)

        box.add(JLabel("Bearer Token:"))
        bearerField = JTextField(getattr(self, prefix + "Bearer"), 40)
        setattr(self, prefix + "BearerField", bearerField)
        box.add(bearerField)

        box.add(JLabel("Cookie header value:"))
        cookieField = JTextField(getattr(self, prefix + "Cookie"), 40)
        setattr(self, prefix + "CookieField", cookieField)
        box.add(cookieField)

        box.add(JLabel("CSRF Token value:"))
        csrfField = JTextField(getattr(self, prefix + "Csrf"), 40)
        setattr(self, prefix + "CsrfField", csrfField)
        box.add(csrfField)

        return box

    # ---------- settings persistence ----------

    def saveSettings(self, event):
        self.adminBearer = self.adminBearerField.getText()
        self.adminCookie = self.adminCookieField.getText()
        self.adminCsrf = self.adminCsrfField.getText()

        self.userBearer = self.userBearerField.getText()
        self.userCookie = self.userCookieField.getText()
        self.userCsrf = self.userCsrfField.getText()

        # strip any colon the user typed by mistake, e.g. "X-CSRF-Token:" -> "X-CSRF-Token"
        self.csrfHeaderName = (self.csrfHeaderField.getText() or "X-CSRF-Token").rstrip(":").strip()
        self.csrfHeaderField.setText(self.csrfHeaderName)

        c = self._callbacks
        c.saveExtensionSetting("admin_bearer", self.adminBearer)
        c.saveExtensionSetting("admin_cookie", self.adminCookie)
        c.saveExtensionSetting("admin_csrf", self.adminCsrf)

        c.saveExtensionSetting("user_bearer", self.userBearer)
        c.saveExtensionSetting("user_cookie", self.userCookie)
        c.saveExtensionSetting("user_csrf", self.userCsrf)

        c.saveExtensionSetting("csrf_header_name", self.csrfHeaderName)
        c.saveExtensionSetting("chk_bearer", "1" if self.chkBearer.isSelected() else "0")
        c.saveExtensionSetting("chk_cookie", "1" if self.chkCookie.isSelected() else "0")
        c.saveExtensionSetting("chk_csrf", "1" if self.chkCsrf.isSelected() else "0")

    def getTabCaption(self):
        return "Cookie Switcher v2"

    def getUiComponent(self):
        return self._panel

    # ---------- context menu ----------

    def createMenuItems(self, invocation):
        menuList = ArrayList()
        ctx = invocation.getInvocationContext()
        if ctx in (invocation.CONTEXT_MESSAGE_EDITOR_REQUEST, invocation.CONTEXT_MESSAGE_VIEWER_REQUEST):
            adminItem = JMenuItem("Switch to Admin", actionPerformed=lambda e: self.applyProfile(invocation, "admin"))
            userItem = JMenuItem("Switch to User", actionPerformed=lambda e: self.applyProfile(invocation, "user"))
            menuList.add(adminItem)
            menuList.add(userItem)
        return menuList

    def _getCsrfHeaderName(self):
        # always strip a trailing colon the user might type, so we never build "Name::"
        return (self.csrfHeaderField.getText() or "X-CSRF-Token").rstrip(":").strip()

    def applyProfile(self, invocation, prefix):
        bearer = getattr(self, prefix + "BearerField").getText()
        cookie = getattr(self, prefix + "CookieField").getText()
        csrf = getattr(self, prefix + "CsrfField").getText()
        csrfHeaderName = self._getCsrfHeaderName()

        doBearer = self.chkBearer.isSelected()
        doCookie = self.chkCookie.isSelected()
        doCsrf = self.chkCsrf.isSelected()

        messages = invocation.getSelectedMessages()
        if not messages:
            return

        for msg in messages:
            request = msg.getRequest()
            info = self._helpers.analyzeRequest(msg.getHttpService(), request)
            headers = list(info.getHeaders())
            bodyOffset = info.getBodyOffset()
            body = request[bodyOffset:]

            newHeaders = []
            gotBearer = gotCookie = gotCsrf = False

            for h in headers:
                if ":" not in h:
                    newHeaders.append(h)
                    continue

                headerName = h.split(":", 1)[0].strip().lower()

                if doBearer and headerName == "authorization":
                    newHeaders.append("Authorization: Bearer " + bearer)
                    gotBearer = True
                elif doCookie and headerName == "cookie":
                    newHeaders.append("Cookie: " + cookie)
                    gotCookie = True
                elif doCsrf and headerName == csrfHeaderName.lower():
                    newHeaders.append(csrfHeaderName + ": " + csrf)
                    gotCsrf = True
                else:
                    newHeaders.append(h)

            if doBearer and not gotBearer:
                newHeaders.append("Authorization: Bearer " + bearer)
            if doCookie and not gotCookie:
                newHeaders.append("Cookie: " + cookie)
            if doCsrf and not gotCsrf:
                newHeaders.append(csrfHeaderName + ": " + csrf)

            # dedupe safety net: never let two headers with the same name survive
            lastIndexForName = {}
            for idx, h in enumerate(newHeaders):
                if ":" in h:
                    lastIndexForName[h.split(":", 1)[0].strip().lower()] = idx
            dedupedHeaders = []
            for idx, h in enumerate(newHeaders):
                if ":" not in h:
                    dedupedHeaders.append(h)
                    continue
                name = h.split(":", 1)[0].strip().lower()
                if lastIndexForName[name] == idx:
                    dedupedHeaders.append(h)

            newMessage = self._helpers.buildHttpMessage(dedupedHeaders, body)
            msg.setRequest(newMessage)

    # ---------- hotkey path: operate on raw editor text instead of IHttpRequestResponse ----------

    def applyProfileToRawText(self, rawText, prefix):
        bearer = getattr(self, prefix + "BearerField").getText()
        cookie = getattr(self, prefix + "CookieField").getText()
        csrf = getattr(self, prefix + "CsrfField").getText()
        csrfHeaderName = self._getCsrfHeaderName()

        doBearer = self.chkBearer.isSelected()
        doCookie = self.chkCookie.isSelected()
        doCsrf = self.chkCsrf.isSelected()

        lineEnding = "\r\n" if "\r\n" in rawText else "\n"
        parts = rawText.split(lineEnding + lineEnding, 1)
        headerBlock = parts[0]
        rest = lineEnding + lineEnding + parts[1] if len(parts) > 1 else ""

        lines = headerBlock.split(lineEnding)
        if not lines:
            return None

        newLines = [lines[0]]
        gotBearer = gotCookie = gotCsrf = False

        for line in lines[1:]:
            if ":" not in line:
                newLines.append(line)
                continue
            headerName = line.split(":", 1)[0].strip().lower()

            if doBearer and headerName == "authorization":
                newLines.append("Authorization: Bearer " + bearer)
                gotBearer = True
            elif doCookie and headerName == "cookie":
                newLines.append("Cookie: " + cookie)
                gotCookie = True
            elif doCsrf and headerName == csrfHeaderName.lower():
                newLines.append(csrfHeaderName + ": " + csrf)
                gotCsrf = True
            else:
                newLines.append(line)

        if doBearer and not gotBearer:
            newLines.append("Authorization: Bearer " + bearer)
        if doCookie and not gotCookie:
            newLines.append("Cookie: " + cookie)
        if doCsrf and not gotCsrf:
            newLines.append(csrfHeaderName + ": " + csrf)

        lastIndexForName = {}
        for idx, line in enumerate(newLines):
            if ":" in line:
                lastIndexForName[line.split(":", 1)[0].strip().lower()] = idx
        deduped = []
        for idx, line in enumerate(newLines):
            if ":" not in line:
                deduped.append(line)
                continue
            name = line.split(":", 1)[0].strip().lower()
            if lastIndexForName[name] == idx:
                deduped.append(line)

        return lineEnding.join(deduped) + rest
