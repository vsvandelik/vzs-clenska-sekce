function convertCzechDate(date) {
    return moment(date, "DD. MM. YYYY hh:mm").toDate()
}