function convertCzechDate(date) {
    return moment(date, "D. M. YYYY hh:mm").toDate()
}