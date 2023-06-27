function setReportValidity(object, txt, report = false) {
    object.setCustomValidity(txt)
    if (report)
        object.reportValidity()
}