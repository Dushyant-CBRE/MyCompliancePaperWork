const roles = [
    { role: 'Compliance Officer', count: 4, permissions: 'Full access' },
    { role: 'Site Manager', count: 12, permissions: 'View only' },
    { role: 'Vendor', count: 28, permissions: 'Upload only' },
];

export function RolesCard() {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">User Roles &amp; Permissions</h3>
            <div className="space-y-3">
                {roles.map((item) => (
                    <div
                        key={item.role}
                        className="flex items-center justify-between p-4 bg-muted rounded-lg"
                    >
                        <div>
                            <p className="text-sm font-medium">{item.role}</p>
                            <p className="text-sm text-muted-foreground mt-0.5">
                                {item.count} users
                            </p>
                        </div>
                        <span className="px-3 py-1 bg-background rounded text-sm">
                            {item.permissions}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
