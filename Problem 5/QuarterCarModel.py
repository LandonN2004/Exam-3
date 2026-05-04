#Landon Norris
# Exam 3 Problem 2
# #region imports
from scipy.integrate import odeint
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import numpy as np
import math
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
#endregion


#region specialized graphic items
class MassBlock(qtw.QGraphicsItem):
    def __init__(self, CenterX, CenterY, width=30, height=10,
                 parent=None, pen=None, brush=None, name='CarBody', mass=10):
        super().__init__(parent)
        self.x = CenterX
        self.y = CenterY
        self.pen = pen
        self.brush = brush
        self.width = width
        self.height = height
        self.top = self.y - self.height / 2
        self.left = self.x - self.width / 2
        self.rect = qtc.QRectF(self.left, self.top, self.width, self.height)
        self.name = name
        self.mass = mass
        self.transformation = qtg.QTransform()
        stTT = self.name + "\nx={:0.3f}, y={:0.3f}\nmass = {:0.3f}".format(
            self.x, self.y, self.mass
        )
        self.setToolTip(stTT)

    def boundingRect(self):
        return self.transformation.mapRect(self.rect)

    def paint(self, painter, option, widget=None):
        self.transformation.reset()

        if self.pen is not None:
            painter.setPen(self.pen)

        if self.brush is not None:
            painter.setBrush(self.brush)

        self.top = -self.height / 2
        self.left = -self.width / 2
        self.rect = qtc.QRectF(self.left, self.top, self.width, self.height)

        painter.drawRect(self.rect)

        self.transformation.translate(self.x, self.y)
        self.setTransform(self.transformation)
        self.transformation.reset()


class Wheel(qtw.QGraphicsItem):
    def __init__(self, CenterX, CenterY, radius=10,
                 parent=None, pen=None, wheelBrush=None,
                 massBrush=None, name='Wheel', mass=10):
        super().__init__(parent)
        self.x = CenterX
        self.y = CenterY
        self.pen = pen
        self.brush = wheelBrush
        self.radius = radius
        self.rect = qtc.QRectF(
            self.x - self.radius,
            self.y - self.radius,
            self.radius * 2,
            self.radius * 2
        )
        self.name = name
        self.mass = mass
        self.transformation = qtg.QTransform()

        stTT = self.name + "\nx={:0.3f}, y={:0.3f}\nmass = {:0.3f}".format(
            self.x, self.y, self.mass
        )
        self.setToolTip(stTT)

        self.massBlock = MassBlock(
            CenterX,
            CenterY,
            width=2 * radius * 0.85,
            height=radius / 3,
            pen=pen,
            brush=massBrush,
            name="Wheel Mass",
            mass=mass
        )

    def boundingRect(self):
        return self.transformation.mapRect(self.rect)

    def addToScene(self, scene):
        scene.addItem(self)
        scene.addItem(self.massBlock)

    def paint(self, painter, option, widget=None):
        self.transformation.reset()

        if self.pen is not None:
            painter.setPen(self.pen)

        if self.brush is not None:
            painter.setBrush(self.brush)

        self.rect = qtc.QRectF(
            -self.radius,
            -self.radius,
            self.radius * 2,
            self.radius * 2
        )

        painter.drawEllipse(self.rect)

        self.transformation.translate(self.x, self.y)
        self.setTransform(self.transformation)
        self.transformation.reset()
#endregion


#region MVC for quarter car model
class CarModel():
    def __init__(self):
        self.results = None

        self.tmax = 3.0
        self.t = np.linspace(0, self.tmax, 200)
        self.tramp = 1.0
        self.angrad = 0.1
        self.ymag = 6.0 / (12.0 * 3.3)
        self.yangdeg = 45.0

        self.m1 = 450.0
        self.m2 = 20.0
        self.c1 = 4500.0
        self.k1 = 15000.0
        self.k2 = 90000.0
        self.v = 120.0

        self.g = 9.81
        self.inch = 0.0254

        self.mink1 = self.m1 * self.g / (6.0 * self.inch)
        self.maxk1 = self.m1 * self.g / (3.0 * self.inch)

        self.mink2 = (self.m1 + self.m2) * self.g / (1.5 * self.inch)
        self.maxk2 = (self.m1 + self.m2) * self.g / (0.75 * self.inch)

        self.accel = None
        self.accelMax = 0.0
        self.accelLim = 2.0
        self.SSE = 0.0

        self.roadData = None
        self.force_k1 = None
        self.force_c1 = None
        self.force_k2 = None


class CarView():
    def __init__(self, args):
        self.input_widgets, self.display_widgets = args

        self.le_m1, self.le_v, self.le_k1, self.le_c1, self.le_m2, self.le_k2, self.le_ang, \
            self.le_tmax, self.chk_IncludeAccel = self.input_widgets

        self.gv_Schematic, self.chk_LogX, self.chk_LogY, self.chk_LogAccel, \
            self.chk_ShowAccel, self.lbl_MaxMinInfo, self.layout_horizontal_main = self.display_widgets

        self.tabs = qtw.QTabWidget()
        self.layout_horizontal_main.addWidget(self.tabs)

        self.position_tab = qtw.QWidget()
        self.position_layout = qtw.QVBoxLayout(self.position_tab)

        self.figure = Figure(tight_layout=True, frameon=True, facecolor='none')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.position_layout.addWidget(self.canvas)

        self.ax = self.figure.add_subplot()
        self.ax1 = self.ax.twinx()

        self.tabs.addTab(self.position_tab, "Position vs. time")

        self.force_tab = qtw.QWidget()
        self.force_layout = qtw.QVBoxLayout(self.force_tab)

        self.force_figure = Figure(tight_layout=True, frameon=True, facecolor='none')
        self.force_canvas = FigureCanvasQTAgg(self.force_figure)
        self.force_layout.addWidget(self.force_canvas)

        self.force_ax = self.force_figure.add_subplot()

        self.tabs.addTab(self.force_tab, "Force vs. time")

        self.buildScene()

    def updateView(self, model=None):
        self.le_m1.setText("{:0.2f}".format(model.m1))
        self.le_v.setText("{:0.2f}".format(model.v))
        self.le_k1.setText("{:0.2f}".format(model.k1))
        self.le_c1.setText("{:0.2f}".format(model.c1))
        self.le_m2.setText("{:0.2f}".format(model.m2))
        self.le_k2.setText("{:0.2f}".format(model.k2))
        self.le_ang.setText("{:0.2f}".format(model.yangdeg))
        self.le_tmax.setText("{:0.2f}".format(model.tmax))

        stTmp = "k1_min = {:0.2f}, k1_max = {:0.2f}\n".format(model.mink1, model.maxk1)
        stTmp += "k2_min = {:0.2f}, k2_max = {:0.2f}\n".format(model.mink2, model.maxk2)
        stTmp += "SSE = {:0.4f}\nMax Accel = {:0.3f} g".format(model.SSE, model.accelMax)

        self.lbl_MaxMinInfo.setText(stTmp)

        self.doPlot(model)

    def buildScene(self):
        self.scene = qtw.QGraphicsScene()
        self.scene.setObjectName("MyScene")
        self.scene.setSceneRect(-200, -200, 400, 400)

        self.gv_Schematic.setScene(self.scene)

        self.setupPensAndBrushes()

        self.Wheel = Wheel(
            0,
            50,
            50,
            pen=self.penWheel,
            wheelBrush=self.brushWheel,
            massBrush=self.brushMass,
            name="Wheel"
        )

        self.CarBody = MassBlock(
            0,
            -70,
            100,
            30,
            pen=self.penWheel,
            brush=self.brushMass,
            name="Car Body",
            mass=150
        )

        self.Wheel.addToScene(self.scene)
        self.scene.addItem(self.CarBody)

        pen = qtg.QPen(qtg.QColor("black"))
        pen.setWidth(2)

        self.scene.addLine(-150, 115, 150, 85, pen)
        self.scene.addLine(-50, -55, -25, 5, pen)
        self.scene.addLine(50, -55, 25, 5, pen)

        self.scene.addText("Suspension").setPos(55, -45)
        self.scene.addText("Tire").setPos(55, 55)
        self.scene.addText("Road").setPos(80, 95)
        self.scene.addText("Car Body").setPos(-35, -115)
        self.scene.addText("Wheel").setPos(-25, 100)

    def setupPensAndBrushes(self):
        self.penWheel = qtg.QPen(qtg.QColor("orange"))
        self.penWheel.setWidth(1)
        self.brushWheel = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))
        self.brushMass = qtg.QBrush(qtg.QColor(200, 200, 200, 128))

    def doPlot(self, model=None):
        if model.results is None:
            return

        ax = self.ax
        ax1 = self.ax1

        ax.clear()
        ax1.clear()

        t = model.t
        ycar = model.results[:, 0]
        ywheel = model.results[:, 2]
        accel = model.accel
        yroad = model.roadData

        if self.chk_LogX.isChecked():
            ax.set_xlim(0.001, model.tmax)
            ax.set_xscale('log')
        else:
            ax.set_xlim(0.0, model.tmax)
            ax.set_xscale('linear')

        ymax = max(ycar.max(), ywheel.max(), yroad.max())

        if self.chk_LogY.isChecked():
            ax.set_ylim(0.0001, ymax * 1.05)
            ax.set_yscale('log')
        else:
            ax.set_ylim(0.0, ymax * 1.05)
            ax.set_yscale('linear')

        ax.plot(t, yroad, 'k--', label='Road Position')
        ax.plot(t, ycar, 'b-', label='Body Position')
        ax.plot(t, ywheel, 'r-', label='Wheel Position')

        if self.chk_ShowAccel.isChecked():
            ax1.plot(t, accel, 'g-', label='Body Accel')
            ax1.axhline(y=model.accelLim, color='orange')
            ax1.axhline(y=-model.accelLim, color='orange')
            ax1.set_yscale('log' if self.chk_LogAccel.isChecked() else 'linear')

        ax.set_ylabel("Vertical Position (m)", fontsize='large')
        ax.set_xlabel("time (s)", fontsize='large')
        ax1.set_ylabel("Body Accel (g)", fontsize='large')

        ax.legend(loc='upper left')

        ax.axvline(x=model.tramp)
        ax.axhline(y=model.ymag)

        ax.tick_params(axis='both', which='both', direction='in', top=True, labelsize='large')
        ax1.tick_params(axis='both', which='both', direction='in', right=True, labelsize='large')

        self.canvas.draw()
        self.doForcePlot(model)

    def doForcePlot(self, model=None):
        if model.results is None:
            return

        ax = self.force_ax
        ax.clear()

        t = model.t

        ax.plot(t, model.force_k1, label="Suspension Spring Force k1")
        ax.plot(t, model.force_c1, label="Dashpot Force c1")
        ax.plot(t, model.force_k2, label="Tire Spring Force k2")

        ax.set_title("Force vs. Time")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("Force (N)")
        ax.grid(True)
        ax.legend()

        self.force_canvas.draw()


class CarController():
    def __init__(self, args):
        self.input_widgets, self.display_widgets = args

        self.le_m1, self.le_v, self.le_k1, self.le_c1, self.le_m2, self.le_k2, self.le_ang, \
            self.le_tmax, self.chk_IncludeAccel = self.input_widgets

        self.gv_Schematic, self.chk_LogX, self.chk_LogY, self.chk_LogAccel, \
            self.chk_ShowAccel, self.lbl_MaxMinInfo, self.layout_horizontal_main = self.display_widgets

        self.model = CarModel()
        self.view = CarView(args)

    def ode_system(self, X, t):
        if t < self.model.tramp:
            y = self.model.ymag * (t / self.model.tramp)
        else:
            y = self.model.ymag

        x1 = X[0]
        x1dot = X[1]
        x2 = X[2]
        x2dot = X[3]

        x1ddot = (
            -self.model.c1 * (x1dot - x2dot)
            - self.model.k1 * (x1 - x2)
        ) / self.model.m1

        x2ddot = (
            self.model.c1 * (x1dot - x2dot)
            + self.model.k1 * (x1 - x2)
            - self.model.k2 * (x2 - y)
        ) / self.model.m2

        return [x1dot, x1ddot, x2dot, x2ddot]

    def calculate(self, doCalc=True):
        self.model.m1 = float(self.le_m1.text())
        self.model.m2 = float(self.le_m2.text())
        self.model.c1 = float(self.le_c1.text())
        self.model.k1 = float(self.le_k1.text())
        self.model.k2 = float(self.le_k2.text())
        self.model.v = float(self.le_v.text())

        self.model.mink1 = self.model.m1 * self.model.g / (6.0 * self.model.inch)
        self.model.maxk1 = self.model.m1 * self.model.g / (3.0 * self.model.inch)

        self.model.mink2 = (self.model.m1 + self.model.m2) * self.model.g / (1.5 * self.model.inch)
        self.model.maxk2 = (self.model.m1 + self.model.m2) * self.model.g / (0.75 * self.model.inch)

        self.model.ymag = 6.0 / (12.0 * 3.3)
        self.model.yangdeg = float(self.le_ang.text())
        self.model.tmax = float(self.le_tmax.text())

        if doCalc:
            self.doCalc()

        self.SSE((self.model.k1, self.model.c1, self.model.k2), optimizing=False)
        self.view.updateView(self.model)

    def doCalc(self, doPlot=True, doAccel=True):
        v = 1000.0 * self.model.v / 3600.0
        self.model.angrad = self.model.yangdeg * math.pi / 180.0

        self.model.tramp = self.model.ymag / (math.sin(self.model.angrad) * v)

        self.model.t = np.linspace(0, self.model.tmax, 2000)

        ic = [0, 0, 0, 0]

        self.model.results = odeint(self.ode_system, ic, self.model.t)

        if doAccel:
            self.calcAccel()

        self.calcForces()

        if doPlot:
            self.doPlot()

    def calcAccel(self):
        N = len(self.model.t)
        self.model.accel = np.zeros(shape=N)
        vel = self.model.results[:, 1]

        for i in range(N):
            if i == N - 1:
                h = self.model.t[i] - self.model.t[i - 1]
                self.model.accel[i] = (vel[i] - vel[i - 1]) / (9.81 * h)
            else:
                h = self.model.t[i + 1] - self.model.t[i]
                self.model.accel[i] = (vel[i + 1] - vel[i]) / (9.81 * h)

        self.model.accelMax = np.max(np.abs(self.model.accel))

        return True

    def calcForces(self):
        t = self.model.t

        x1 = self.model.results[:, 0]
        x1dot = self.model.results[:, 1]
        x2 = self.model.results[:, 2]
        x2dot = self.model.results[:, 3]

        yroad = np.zeros_like(t)

        for i in range(len(t)):
            if t[i] < self.model.tramp:
                yroad[i] = self.model.ymag * (t[i] / self.model.tramp)
            else:
                yroad[i] = self.model.ymag

        self.model.roadData = yroad

        self.model.force_k1 = self.model.k1 * (x1 - x2)
        self.model.force_c1 = self.model.c1 * (x1dot - x2dot)
        self.model.force_k2 = self.model.k2 * (x2 - yroad)

    def OptimizeSuspension(self):
        self.calculate(doCalc=False)

        x0 = np.array([
            self.model.k1,
            self.model.c1,
            self.model.k2
        ])

        answer = minimize(
            self.SSE,
            x0,
            method='Nelder-Mead',
            options={
                'maxiter': 300,
                'xatol': 1e-3,
                'fatol': 1e-3,
                'disp': False
            }
        )

        self.model.k1 = answer.x[0]
        self.model.c1 = answer.x[1]
        self.model.k2 = answer.x[2]

        self.doCalc()
        self.SSE((self.model.k1, self.model.c1, self.model.k2), optimizing=False)
        self.view.updateView(self.model)

    def SSE(self, vals, optimizing=True):
        k1, c1, k2 = vals

        self.model.k1 = k1
        self.model.c1 = c1
        self.model.k2 = k2

        self.doCalc(doPlot=False)

        SSE = 0.0

        for i in range(len(self.model.results[:, 0])):
            t = self.model.t[i]
            y = self.model.results[:, 0][i]

            if t < self.model.tramp:
                ytarget = self.model.ymag * (t / self.model.tramp)
            else:
                ytarget = self.model.ymag

            SSE += (y - ytarget) ** 2

        if optimizing:
            if k1 < self.model.mink1:
                SSE += 1e6 * (self.model.mink1 - k1) ** 2

            if k1 > self.model.maxk1:
                SSE += 1e6 * (k1 - self.model.maxk1) ** 2

            if c1 < 10:
                SSE += 1e6 * (10 - c1) ** 2

            if k2 < self.model.mink2:
                SSE += 1e6 * (self.model.mink2 - k2) ** 2

            if k2 > self.model.maxk2:
                SSE += 1e6 * (k2 - self.model.maxk2) ** 2

            if self.chk_IncludeAccel.isChecked():
                if self.model.accelMax > self.model.accelLim:
                    SSE += 1e5 * (self.model.accelMax - self.model.accelLim) ** 2

        self.model.SSE = SSE

        return SSE

    def doPlot(self):
        self.view.doPlot(self.model)
#endregion


def main():
    print("Run Car_app.py to launch the GUI.")


if __name__ == '__main__':
    main()