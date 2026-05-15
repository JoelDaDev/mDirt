# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'attributelFySsz.ui'
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
    QLabel, QPushButton, QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(307, 143)
        self.gridLayout = QGridLayout(Form)
        self.gridLayout.setObjectName(u"gridLayout")
        self.label_4 = QLabel(Form)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout.addWidget(self.label_4, 3, 1, 1, 1)

        self.amountOperationBox = QComboBox(Form)
        self.amountOperationBox.addItem("")
        self.amountOperationBox.addItem("")
        self.amountOperationBox.addItem("")
        self.amountOperationBox.setObjectName(u"amountOperationBox")

        self.gridLayout.addWidget(self.amountOperationBox, 3, 2, 1, 1)

        self.label = QLabel(Form)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 1, 1, 1)

        self.label_3 = QLabel(Form)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout.addWidget(self.label_3, 2, 1, 1, 1)

        self.amountSpinBox = QDoubleSpinBox(Form)
        self.amountSpinBox.setObjectName(u"amountSpinBox")
        self.amountSpinBox.setDecimals(6)
        self.amountSpinBox.setMinimum(0.000000000000000)

        self.gridLayout.addWidget(self.amountSpinBox, 2, 2, 1, 1)

        self.attributeLabel = QLabel(Form)
        self.attributeLabel.setObjectName(u"attributeLabel")

        self.gridLayout.addWidget(self.attributeLabel, 0, 2, 1, 1)

        self.attributeRemove = QPushButton(Form)
        self.attributeRemove.setObjectName(u"attributeRemove")
        icon = QIcon(QIcon.fromTheme(QIcon.ThemeIcon.ListRemove))
        self.attributeRemove.setIcon(icon)

        self.gridLayout.addWidget(self.attributeRemove, 6, 2, 1, 1)

        self.attributeSign = QComboBox(Form)
        self.attributeSign.addItem("")
        self.attributeSign.addItem("")
        self.attributeSign.setObjectName(u"attributeSign")

        self.gridLayout.addWidget(self.attributeSign, 6, 1, 1, 1)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_4.setText(QCoreApplication.translate("Form", u"Operation", None))
        self.amountOperationBox.setItemText(0, QCoreApplication.translate("Form", u"add_value", None))
        self.amountOperationBox.setItemText(1, QCoreApplication.translate("Form", u"add_multiplied_base", None))
        self.amountOperationBox.setItemText(2, QCoreApplication.translate("Form", u"add_multiplied_total", None))

#if QT_CONFIG(tooltip)
        self.amountOperationBox.setToolTip(QCoreApplication.translate("Form", u"The operation to apply", None))
#endif // QT_CONFIG(tooltip)
        self.label.setText(QCoreApplication.translate("Form", u"Attribute:", None))
        self.label_3.setText(QCoreApplication.translate("Form", u"Amount:", None))
#if QT_CONFIG(tooltip)
        self.amountSpinBox.setToolTip(QCoreApplication.translate("Form", u"Amount to modify the attribute by.", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.attributeLabel.setToolTip(QCoreApplication.translate("Form", u"The id of the attribute to modify.", None))
#endif // QT_CONFIG(tooltip)
        self.attributeLabel.setText("")
#if QT_CONFIG(tooltip)
        self.attributeRemove.setToolTip(QCoreApplication.translate("Form", u"Remove this Attribute", None))
#endif // QT_CONFIG(tooltip)
        self.attributeRemove.setText("")
        self.attributeSign.setItemText(0, QCoreApplication.translate("Form", u"+", None))
        self.attributeSign.setItemText(1, QCoreApplication.translate("Form", u"-", None))

#if QT_CONFIG(tooltip)
        self.attributeSign.setToolTip(QCoreApplication.translate("Form", u"Whether the amount done to the attribute is negative or positive.", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

