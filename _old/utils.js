
export function writeJson(filePath, obj) {
  Deno.writeTextFileSync(filePath, JSON.stringify(obj))
  return filePath
}

export function readJson(filePath) {
  return JSON.parse(Deno.readTextFileSync(filePath))
}

export function getMonthDifference(startDate, endDate) {
  return (
    endDate.getMonth() -
    startDate.getMonth() +
    12 * (endDate.getFullYear() - startDate.getFullYear())
  )
}


export function addMonths(isoDate, numberMonths) {
  var dateObject = new Date(isoDate), day = dateObject.getDate(); // returns day of the month number

  // avoid date calculation errors
  dateObject.setHours(20)

  // add months and set date to last day of the correct month
  dateObject.setMonth(dateObject.getMonth() + numberMonths + 1, 0)

  // set day number to min of either the original one or last day of month
  dateObject.setDate(Math.min(day, dateObject.getDate()))

  return dateObject.toISOString().split('T')[0]
}