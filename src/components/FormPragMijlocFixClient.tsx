import type { FC } from 'hono/jsx'
import { useState } from 'hono/jsx'


export const FormPragMijlocFix: FC = () => {

    let [deleteAlert, setDeleteAlert] = useState(false)

    return (

        <>
            {
                deleteAlert
                    ?
                    <div className="flex justify-center">
                        <div role="alert" className="alert alert-warning max-w-fit my-12">
                            <svg
                                xmlns="http://www.w3.org/2000/svg"
                                className="h-6 w-6 shrink-0 stroke-current"
                                fill="none"
                                viewBox="0 0 24 24">
                                <path
                                    strokeLinecap="round"
                                    strokeLinejoin="round"
                                    strokeWidth="2"
                                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            <span>Sigur vrei sa stergi?</span>
                            <div className="space-x-2">
                                <button className="btn btn-sm">M-am razgandit</button>
                                <button className="btn btn-sm btn-error">Da, sterge acum!</button>
                            </div>
                        </div>
                    </div>
                    : null

            }


            <div>

                <form className="flex gap-6 mt-12">

                    <label className="form-control w-full max-w-xs">
                        <div className="label">
                            <span className="label-text font-bold">Anul:</span>
                        </div>
                        <input type="number" placeholder="Anul" className="input input-bordered w-full max-w-xs" />
                        <div className="label">
                            <span className="label-text-alt text-gray-400">
                                Anul pentru care este valid pragul de mijloace fixe.
                            </span>
                        </div>
                    </label>

                    <label className="form-control w-full max-w-xs">
                        <div className="label">
                            <span className="label-text font-bold">Prag mijloc fix:</span>
                        </div>
                        <input type="number" placeholder="Suma in RON" className="input input-bordered w-full max-w-xs" />
                        <div className="label">
                            <span className="label-text-alt text-gray-400">
                                Suma peste care achizitia trebuie amortizata in timp.
                            </span>
                        </div>
                    </label>

                    <button type="submit" className="btn btn-primary mt-[34px]">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" className="size-5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                        </svg>
                    </button>

                </form>

                <div className="overflow-x-auto">
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Anul</th>
                                <th>Prag</th>
                                <th>Sterge</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr className="bg-base-200">
                                <td>2022</td>
                                <td>2500</td>
                                <td className="w-6">
                                    <button onClick={() => setDeleteAlert(!deleteAlert)} className="btn btn-xs bg-white text-red-500">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" className="size-4">
                                            <path stroke-linecap="round" stroke-linejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                                        </svg>
                                    </button>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

        </>

    )
}


