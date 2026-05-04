# Landon Norris
# Exam 3 Problem 6
#region imports
import math
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg
from GraphicsView_App import RigidLink, RigidPivotPoint
#endregion


class Position():
    def __init__(self, pos=None, x=None, y=None, z=None):
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0

        if pos is not None:
            self.x, self.y, self.z = pos

        self.x = x if x is not None else self.x
        self.y = y if y is not None else self.y
        self.z = z if z is not None else self.z

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.z == other.z

    def __add__(self, other):
        return Position((self.x + other.x, self.y + other.y, self.z + other.z))

    def __sub__(self, other):
        return Position((self.x - other.x, self.y - other.y, self.z - other.z))

    def mag(self):
        return (self.x ** 2 + self.y ** 2 + self.z ** 2) ** 0.5

    def getAngleRad(self):
        length = self.mag()

        if length <= 0.0:
            return 0.0

        if self.y >= 0.0:
            return math.acos(self.x / length)

        return 2.0 * math.pi - math.acos(self.x / length)


class Rectangle():
    def __init__(self, top=None, left=None, bottom=None, right=None):
        self.top = 0 if top is None else top
        self.left = 0 if left is None else left
        self.bottom = 0 if bottom is None else bottom
        self.right = 0 if right is None else right

    def height(self):
        return self.top - self.bottom

    def width(self):
        return self.right - self.left

    def centerY(self):
        return self.bottom + self.height() / 2.0

    def centerX(self):
        return self.left + self.width() / 2.0


class Material():
    def __init__(self, uts=None, ys=None, modulus=None, staticFactor=None):
        self.uts = uts
        self.ys = ys
        self.E = modulus
        self.staticFactor = staticFactor


class Node():
    def __init__(self, name=None, position=None):
        self.name = name
        self.position = position if position is not None else Position()
        self.graphic = RigidPivotPoint(self.position.x, self.position.y, 10, 30)
        self.reactionY = 0.0


class Link():
    def __init__(
        self,
        name="",
        node1="1",
        node2="2",
        material="steel",
        width=2.0,
        thickness=0.5,
    ):
        self.name = name
        self.node1_Name = node1
        self.node2_Name = node2

        self.material = material.lower()
        self.width = float(width)
        self.thickness = float(thickness)

        self.length = 0.0
        self.angleRad = 0.0
        self.weight = 0.0

        self.graphic = RigidLink(0, 0, 1, 1)
        self.graphic.name = name

    def density(self):
        if self.material.lower() in ["aluminum", "aluminium"]:
            return 0.098
        return 0.283

    def calcWeight(self):
        self.weight = self.density() * self.length * self.width * self.thickness


class TrussModel():
    def __init__(self):
        self.title = None
        self.links = []
        self.nodes = []
        self.material = Material()
        self.rct = Rectangle()
        self.totalWeight = 0.0
        self.leftReaction = 0.0
        self.rightReaction = 0.0

    def getNode(self, name):
        for node in self.nodes:
            if node.name == name:
                return node
        return None

    def getCenterPt(self):
        rct = Rectangle()
        rct.left = self.nodes[0].position.x
        rct.right = self.nodes[0].position.x
        rct.top = self.nodes[0].position.y
        rct.bottom = self.nodes[0].position.y

        for node in self.nodes:
            rct.left = min(rct.left, node.position.x)
            rct.right = max(rct.right, node.position.x)
            rct.top = max(rct.top, node.position.y)
            rct.bottom = min(rct.bottom, node.position.y)

        self.rct = rct


class TrussView():
    def __init__(self):
        self.scene = qtw.QGraphicsScene()

        self.le_LongLinkName = qtw.QLineEdit()
        self.le_LongLinkNode1 = qtw.QLineEdit()
        self.le_LongLinkNode2 = qtw.QLineEdit()
        self.le_LongLinkLength = qtw.QLineEdit()
        self.te_Report = qtw.QTextEdit()
        self.gv = qtw.QGraphicsView()

        self.penLink = qtg.QPen(qtg.QColor("orange"))
        self.penLink.setWidth(2)

        self.penNode = qtg.QPen(qtc.Qt.darkBlue)
        self.penNode.setWidth(1)

        self.penLabel = qtg.QPen(qtc.Qt.darkMagenta)
        self.penLabel.setWidth(1)

        self.penGridLines = qtg.QPen()
        self.penGridLines.setWidth(1)
        self.penGridLines.setColor(qtg.QColor.fromHsv(197, 144, 228, alpha=50))

        self.brushLink = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))
        self.brushPivot = qtg.QBrush(qtg.QColor.fromRgb(215, 215, 215, alpha=128))
        self.brushNode = qtg.QBrush(qtg.QColor.fromCmyk(0, 0, 255, 0, alpha=100))
        self.brushGrid = qtg.QBrush(qtg.QColor.fromHsv(87, 98, 245, alpha=128))
        self.brushRoller = qtg.QBrush(qtg.QColor.fromRgb(180, 180, 180, alpha=160))

    def setDisplayWidgets(self, args):
        self.te_Report = args[0]
        self.le_LongLinkName = args[1]
        self.le_LongLinkNode1 = args[2]
        self.le_LongLinkNode2 = args[3]
        self.le_LongLinkLength = args[4]
        self.gv = args[5]
        self.gv.setScene(self.scene)

    def displayReport(self, truss=None):
        st = "\tTruss Design Report\n"
        st += "Title:  {}\n".format(truss.title)
        st += "Static Factor of Safety:  {:0.2f}\n".format(truss.material.staticFactor)
        st += "Ultimate Strength:  {:0.2f}\n".format(truss.material.uts)
        st += "Yield Strength:  {:0.2f}\n".format(truss.material.ys)
        st += "Modulus of Elasticity:  {:0.2f}\n".format(truss.material.E)
        st += "_____________Link Summary________________\n"
        st += "Link\t(1)\t(2)\tMat\tWidth\tThk\tLength\tAngle\tWeight\n"

        longest = None

        for link in truss.links:
            if longest is None or link.length > longest.length:
                longest = link

            st += "{}\t{}\t{}\t{}\t{:0.2f}\t{:0.2f}\t{:0.2f}\t{:0.2f}\t{:0.2f}\n".format(
                link.name,
                link.node1_Name,
                link.node2_Name,
                link.material,
                link.width,
                link.thickness,
                link.length,
                link.angleRad,
                link.weight,
            )

        st += "\nLeft Reaction: {:0.2f}\n".format(truss.leftReaction)
        st += "Right Reaction: {:0.2f}\n".format(truss.rightReaction)

        self.te_Report.setText(st)

        if longest is not None:
            self.le_LongLinkName.setText(longest.name)
            self.le_LongLinkLength.setText("{:0.2f}".format(longest.length))
            self.le_LongLinkNode1.setText(longest.node1_Name)
            self.le_LongLinkNode2.setText(longest.node2_Name)

    def buildScene(self, truss=None):
        truss.getCenterPt()
        rct = truss.rct

        rct.left -= 50
        rct.right += 50
        rct.top += 50
        rct.bottom -= 50

        self.scene.clear()
        self.scene.setSceneRect(
            -abs(rct.width()) / 2.0,
            -abs(rct.height()) / 2.0,
            abs(rct.width()),
            abs(rct.height()),
        )

        self.drawAGrid(
            DeltaX=10,
            DeltaY=10,
            Height=abs(rct.height()),
            Width=abs(rct.width()),
            CenterX=0,
            CenterY=0,
        )

        self.drawLinks(truss)
        self.drawNodes(truss)

    def drawAGrid(self, DeltaX=10, DeltaY=10, Height=320, Width=180, CenterX=0, CenterY=0):
        left = CenterX - Width / 2.0
        right = CenterX + Width / 2.0
        top = CenterY - Height / 2.0
        bottom = CenterY + Height / 2.0

        rect = qtw.QGraphicsRectItem(left, top, Width, Height)
        rect.setBrush(self.brushGrid)
        rect.setPen(self.penGridLines)
        self.scene.addItem(rect)

        x = left
        while x <= right:
            line = qtw.QGraphicsLineItem(x, top, x, bottom)
            line.setPen(self.penGridLines)
            self.scene.addItem(line)
            x += DeltaX

        y = top
        while y <= bottom:
            line = qtw.QGraphicsLineItem(left, y, right, y)
            line.setPen(self.penGridLines)
            self.scene.addItem(line)
            y += DeltaY

    def drawLinks(self, truss=None):
        truss.getCenterPt()
        offset = Position(x=truss.rct.centerX(), y=truss.rct.centerY())

        for link in truss.links:
            node1 = truss.getNode(link.node1_Name)
            node2 = truss.getNode(link.node2_Name)

            x1 = node1.position.x - offset.x
            y1 = -(node1.position.y - offset.y)
            x2 = node2.position.x - offset.x
            y2 = -(node2.position.y - offset.y)

            link.graphic = RigidLink(
                x1,
                y1,
                x2,
                y2,
                radius=3,
                pen=self.penLink,
                brush=self.brushLink,
                name="Link " + link.name,
            )

            link.graphic.setData(0, "Link " + link.name)

            tooltip = (
                "Link name = {}\n"
                "start: ({:0.3f}, {:0.3f})\n"
                "end: ({:0.3f}, {:0.3f})\n"
                "length: {:0.3f}\n"
                "angle: {:0.3f}\n"
                "material: {}\n"
                "width: {:0.3f}\n"
                "thickness: {:0.3f}\n"
                "weight: {:0.3f} lb"
            ).format(
                link.name,
                x1,
                y1,
                x2,
                y2,
                link.length,
                link.angleRad,
                link.material,
                link.width,
                link.thickness,
                link.weight,
            )

            link.graphic.setToolTip(tooltip)
            self.scene.addItem(link.graphic)

    def drawNodes(self, truss=None):
        truss.getCenterPt()
        offset = Position(x=truss.rct.centerX(), y=truss.rct.centerY())

        for node in truss.nodes:
            x = node.position.x - offset.x
            y = node.position.y - offset.y

            tooltip = "Node: {}\nVertical Load: {:0.2f} lb".format(node.name, node.reactionY)

            if node.name.lower() == "left":
                node.graphic = RigidPivotPoint(x, -y, 10, 18, brush=self.brushPivot, name=node.name)
                node.graphic.setData(0, "Pin Support: " + node.name)
                node.graphic.setToolTip(tooltip + "\nSupport: Pin")
                self.scene.addItem(node.graphic)

            elif node.name.lower() == "right":
                self.drawRollerSupport(x, -y, node, tooltip)

            else:
                self.drawACircle(
                    centerX=x,
                    centerY=y,
                    Radius=6,
                    pen=self.penNode,
                    brush=self.brushNode,
                    name=node.name,
                    tooltip=tooltip,
                )

            self.drawALabel(x=x - 5, y=y + 15, str=node.name, pen=self.penLabel)

    def drawRollerSupport(self, x, y, node, tooltip):
        points = [
            qtc.QPointF(x, y),
            qtc.QPointF(x - 10, y + 18),
            qtc.QPointF(x + 10, y + 18),
            qtc.QPointF(x, y),
        ]

        tri = qtw.QGraphicsPolygonItem(qtg.QPolygonF(points))
        tri.setBrush(self.brushPivot)
        tri.setPen(self.penNode)
        tri.setData(0, "Roller Support: " + node.name)
        tri.setToolTip(tooltip + "\nSupport: Roller")
        self.scene.addItem(tri)

        roller1 = qtw.QGraphicsEllipseItem(x - 10, y + 19, 6, 6)
        roller2 = qtw.QGraphicsEllipseItem(x + 4, y + 19, 6, 6)

        roller1.setBrush(self.brushRoller)
        roller2.setBrush(self.brushRoller)
        roller1.setPen(self.penNode)
        roller2.setPen(self.penNode)

        roller1.setToolTip(tooltip + "\nSupport: Roller")
        roller2.setToolTip(tooltip + "\nSupport: Roller")

        self.scene.addItem(roller1)
        self.scene.addItem(roller2)

        base = qtw.QGraphicsLineItem(x - 18, y + 28, x + 18, y + 28)
        base.setPen(self.penNode)
        self.scene.addItem(base)

    def drawALabel(self, x, y, str="", pen=None):
        lbl = qtw.QGraphicsTextItem(str)
        width = lbl.boundingRect().width()
        height = lbl.boundingRect().height()

        lbl.setX(x - width / 2.0)
        lbl.setY(-y - height / 2.0)

        if pen is not None:
            lbl.setDefaultTextColor(pen.color())

        self.scene.addItem(lbl)

    def drawACircle(self, centerX, centerY, Radius, brush=None, pen=None, name=None, tooltip=None):
        ellipse = qtw.QGraphicsEllipseItem(
            centerX - Radius,
            -1.0 * (centerY + Radius),
            2 * Radius,
            2 * Radius,
        )

        if pen is not None:
            ellipse.setPen(pen)

        if brush is not None:
            ellipse.setBrush(brush)

        if name is not None:
            ellipse.setData(0, name)

        if tooltip is not None:
            ellipse.setToolTip(tooltip)

        self.scene.addItem(ellipse)


class TrussController():
    def __init__(self):
        self.truss = TrussModel()
        self.view = TrussView()

    def setDisplayWidgets(self, args):
        self.view.setDisplayWidgets(args)

    def installSceneEventFilter(self, obj):
        self.view.scene.installEventFilter(obj)

    def handleSceneEvent(self, obj, event, transform):
        if obj != self.view.scene:
            return None, False

        if event.type() == qtc.QEvent.GraphicsSceneMouseMove:
            scenePos = event.scenePos()

            message = "Mouse Position:  x = {}, y = {}".format(
                round(scenePos.x(), 2),
                round(-scenePos.y(), 2),
            )

            item = self.view.scene.itemAt(scenePos, transform)

            if item is not None and item.data(0) is not None:
                message += " (" + item.data(0) + ")"

            return message, True

        if event.type() == qtc.QEvent.GraphicsSceneWheel:
            return None, True

        return None, False

    def ImportFromFile(self, data):
        self.truss = TrussModel()

        for line in data:
            line = line.strip()

            if len(line) == 0:
                continue

            if line.find("#") == 0:
                continue

            cells = line.split(",")

            if len(cells) <= 1:
                continue

            keyword = cells[0].strip().lower()

            if keyword.find("title") >= 0:
                self.truss.title = cells[1].strip().replace("'", "").replace('"', "")

            elif keyword.find("material") >= 0:
                sut = float(cells[1].strip())
                sy = float(cells[2].strip())
                E = float(cells[3].strip())
                self.truss.material = Material(uts=sut, ys=sy, modulus=E)

            elif keyword.find("static") >= 0:
                static_factor = float(cells[1].strip())
                self.truss.material.staticFactor = static_factor

            elif keyword.find("node") >= 0:
                name = cells[1].strip()
                x = float(cells[2].strip())
                y = float(cells[3].strip())
                self.truss.nodes.append(Node(name=name, position=Position(x=x, y=y)))

            elif keyword.find("link") >= 0:
                name = cells[1].strip()
                node1 = cells[2].strip()
                node2 = cells[3].strip()

                material = "steel"
                width = 2.0
                thickness = 0.5

                if len(cells) > 4:
                    material = cells[4].strip().lower()

                if len(cells) > 5:
                    width = float(cells[5].strip())

                if len(cells) > 6:
                    thickness = float(cells[6].strip())

                self.truss.links.append(
                    Link(
                        name=name,
                        node1=node1,
                        node2=node2,
                        material=material,
                        width=width,
                        thickness=thickness,
                    )
                )

        self.calcLinkVals()
        self.calcTrussWeightAndReactions()
        self.displayReport()
        self.drawTruss()

    def hasNode(self, name):
        for node in self.truss.nodes:
            if node.name == name:
                return True
        return False

    def getNode(self, name):
        return self.truss.getNode(name)

    def calcLinkVals(self):
        for link in self.truss.links:
            node1 = self.getNode(link.node1_Name)
            node2 = self.getNode(link.node2_Name)

            if node1 is not None and node2 is not None:
                r = node2.position - node1.position
                link.length = r.mag()
                link.angleRad = r.getAngleRad()
                link.calcWeight()

    def calcTrussWeightAndReactions(self):
        self.truss.totalWeight = sum(link.weight for link in self.truss.links)

        left_node = self.getNode("Left")
        right_node = self.getNode("Right")

        if left_node is None or right_node is None:
            return

        left_x = left_node.position.x
        right_x = right_node.position.x
        span = right_x - left_x

        if abs(span) < 1.0e-9:
            self.truss.leftReaction = self.truss.totalWeight / 2.0
            self.truss.rightReaction = self.truss.totalWeight / 2.0

        else:
            moment_about_left = 0.0

            for link in self.truss.links:
                node1 = self.getNode(link.node1_Name)
                node2 = self.getNode(link.node2_Name)

                if node1 is None or node2 is None:
                    continue

                x_mid = 0.5 * (node1.position.x + node2.position.x)
                moment_about_left += link.weight * (x_mid - left_x)

            self.truss.rightReaction = moment_about_left / span
            self.truss.leftReaction = self.truss.totalWeight - self.truss.rightReaction

        left_node.reactionY = self.truss.leftReaction
        right_node.reactionY = self.truss.rightReaction

    def displayReport(self):
        self.view.displayReport(truss=self.truss)

    def drawTruss(self):
        self.view.buildScene(truss=self.truss)
#endregion