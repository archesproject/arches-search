import { ref } from "vue";
import { useGettext } from "vue3-gettext";

import { useToast } from "openvue/usetoast";

import { toError } from "@/arches_search/AdvancedSearch/utils/errors.ts";
import { startSearchResultsExport } from "@/arches_search/SimpleSearch/api.ts";
import {
    EXPORT_STATE_IDLE,
    EXPORT_STATE_PENDING,
} from "@/arches_search/SimpleSearch/types.ts";

import type { Ref } from "vue";
import type { ExportState } from "@/arches_search/SimpleSearch/types.ts";

type ExportParameters = Parameters<typeof startSearchResultsExport>[0];

// The export runs in the background; the user hears about its completion
// through an Arches notification, so this only reports whether it started.
export function useResultsExport(): {
    exportState: Ref<ExportState>;
    exportResults(exportParameters: ExportParameters): Promise<void>;
} {
    const { $gettext } = useGettext();
    const toast = useToast();

    const exportState = ref<ExportState>(EXPORT_STATE_IDLE);

    async function exportResults(
        exportParameters: ExportParameters,
    ): Promise<void> {
        exportState.value = EXPORT_STATE_PENDING;
        try {
            await startSearchResultsExport(exportParameters);
            toast.add({
                severity: "success",
                life: 3000,
                summary: $gettext("Your export has started."),
                detail: $gettext(
                    "You will be notified when it is ready to download.",
                ),
            });
        } catch (error) {
            toast.add({
                severity: "error",
                life: 5000,
                summary: $gettext("Export could not be started."),
                detail: toError(error).message,
            });
        } finally {
            exportState.value = EXPORT_STATE_IDLE;
        }
    }

    return { exportState, exportResults };
}
