import type { FC } from 'hono/jsx'


export const PageHeader: FC<{ title: string, description: string }> = ({ title, description }) => {
    return (
        <header class="mb-16 py-12 text-center bg-gray-50 rounded-md">
            <h1 className="text-2xl font-bold mb-2">
                {title}
            </h1>
            <p> {description} </p>
        </header>
    )
}
