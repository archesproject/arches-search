import { type Ref } from "vue";

const PENDING = "pending";
const READY = "ready";

type CacheEntry<T> =
    | { status: typeof PENDING; pending: Promise<T> }
    | { status: typeof READY; value: T };

export type AsyncCache<T> = Ref<Record<string, CacheEntry<T>>>;

export async function getFromCache<T>(
    cache: AsyncCache<T>,
    key: string,
    loader: () => Promise<T>,
): Promise<T> {
    const existing = cache.value[key];

    if (existing?.status === PENDING) {
        return await existing.pending;
    }
    if (existing?.status === READY) {
        return existing.value;
    }

    const pending = loader()
        .then((value) => {
            cache.value = { ...cache.value, [key]: { status: READY, value } };
            return value;
        })
        .catch((error: Error) => {
            const { [key]: _, ...rest } = cache.value;
            cache.value = rest;
            throw error;
        });

    cache.value = { ...cache.value, [key]: { status: PENDING, pending } };
    return await pending;
}
