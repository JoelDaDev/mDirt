# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'attributevWjLMZ.ui'
##
## Created by: Qt User Interface Compiler version 6.11.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QGridLayout,
    QLabel, QSizePolicy, QSpacerItem, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(291, 122)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_4 = QLabel(Form)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 2, 0, 1, 1)

        self.amountOperationBox = QComboBox(Form)
        self.amountOperationBox.addItem("")
        self.amountOperationBox.addItem("")
        self.amountOperationBox.addItem("")
        self.amountOperationBox.setObjectName(u"amountOperationBox")

        self.gridLayout.addWidget(self.amountOperationBox, 2, 1, 1, 1)

        self.attributeLabel = QLabel(Form)
        self.attributeLabel.setObjectName(u"attributeLabel")

        self.gridLayout.addWidget(self.attributeLabel, 0, 1, 1, 1)

        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 1, 0, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.amountSpinBox = QDoubleSpinBox(Form)
        self.amountSpinBox.setObjectName(u"amountSpinBox")
        self.amountSpinBox.setDecimals(6)

        self.gridLayout.addWidget(self.amountSpinBox, 1, 1, 1, 1)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout.addItem(self.verticalSpacer, 3, 0, 1, 2)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Operation", None))
        self.amountOperationBox.setItemText(0, QCoreApplication.translate("Form", u"add_value", None))
        self.amountOperationBox.setItemText(1, QCoreApplication.translate("Form", u"add_multiplied_base", None))
        self.amountOperationBox.setItemText(2, QCoreApplication.translate("Form", u"add_multiplied_total", None))

        self.attributeLabel.setText("")
        self.label_3.setText(QCoreApplication.translate("Form", u"Amount:", None))
        self.label.setText(QCoreApplication.translate("Form", u"Attribute:", None))
    # retranslateUi

