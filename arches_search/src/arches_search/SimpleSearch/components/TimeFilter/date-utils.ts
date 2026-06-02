import dayjs from "dayjs";

export function clamp(value: number, min: number, max: number): number {
    return Math.min(Math.max(value, min), max);
}

export function countDaysBetween(start: Date, end: Date): number {
    const msPerDay = 1000 * 60 * 60 * 24;

    return Math.round((end.getTime() - start.getTime()) / msPerDay);
}

export function normalizeRange(startDate: Date, endDate: Date): [Date, Date] {
    const start = dayjs(startDate).startOf("day");
    const end = dayjs(endDate).startOf("day");

    if (start.isAfter(end)) {
        return [end.toDate(), start.toDate()];
    }

    return [start.toDate(), end.toDate()];
}

export function parseSortableDate(sortableDate: number): Date {
    const year = Math.floor(sortableDate / 10000);
    const monthDay = sortableDate - year * 10000;
    const month = Math.floor(monthDay / 100);
    const day = monthDay % 100;
    const date = new Date(0);

    date.setFullYear(year, month - 1, day);
    date.setHours(0, 0, 0, 0);

    return date;
}

export function toLocalISODateString(date: Date): string {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");

    if (year < 0) {
        return `-${String(-year).padStart(4, "0")}-${month}-${day}`;
    }

    return `${String(year).padStart(4, "0")}-${month}-${day}`;
}

export function startOfYear(year: number): Date {
    const date = new Date(0);

    date.setFullYear(year, 0, 1);
    date.setHours(0, 0, 0, 0);

    return date;
}

export function endOfYear(year: number): Date {
    const date = new Date(0);

    date.setFullYear(year, 11, 31);
    date.setHours(0, 0, 0, 0);

    return date;
}

export function addDays(base: Date, days: number): Date {
    return dayjs(base).add(days, "day").startOf("day").toDate();
}
