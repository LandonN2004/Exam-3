#Landon Norris
# Exam 3 Problem 6
# #region imports
from Truss_GUI import Ui_TrussStructuralDesign
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from Truss_Classes import TrussController
import sys
#endregion


#region class definitions
class MainWindow(Ui_TrussStructuralDesign, qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.controller = TrussController()
        self.controller.setDisplayWidgets(
            (
                self.te_DesignReport,
                self.le_LinkName,
                self.le_Node1Name,
                self.le_Node2Name,
                self.le_LinkLength,
                self.gv_Main,
            )
        )

        self.btn_Open.clicked.connect(self.OpenFile)
        self.spnd_Zoom.valueChanged.connect(self.setZoom)

        # MVC fix: install the filter through the controller, not by reaching into view directly
        self.controller.installSceneEventFilter(self)

        self.gv_Main.setMouseTracking(True)
        self.show()

    def setZoom(self):
        self.gv_Main.resetTransform()
        self.gv_Main.scale(self.spnd_Zoom.value(), self.spnd_Zoom.value())

    def eventFilter(self, obj, event):
        message, handled = self.controller.handleSceneEvent(
            obj=obj,
            event=event,
            transform=self.gv_Main.transform(),
        )

        if message is not None:
            self.lbl_MousePos.setText(message)

        if handled:
            if event.type() == qtc.QEvent.GraphicsSceneWheel:
                if event.delta() > 0:
                    self.spnd_Zoom.stepUp()
                else:
                    self.spnd_Zoom.stepDown()

        return super(MainWindow, self).eventFilter(obj, event)

    def OpenFile(self):
        filename = qtw.QFileDialog.getOpenFileName()[0]

        if len(filename) == 0:
            return

        self.te_Path.setText(filename)

        with open(filename, "r") as file:
            data = file.readlines()

        self.controller.ImportFromFile(data)
#endregion


#region function definitions
def Main():
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    sys.exit(app.exec())
#endregion


#region function calls
if __name__ == "__main__":
    Main()
#endregion