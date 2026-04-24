interface PageHeaderProps {
    title: string;
    subtitle: string;
}

export function PageHeader({ title, subtitle }: PageHeaderProps) {
    return (
        <div className="mb-6">
            <h1>{title}</h1>
            <p className="text-muted-foreground mt-1">{subtitle}</p>
        </div>
    );
}
