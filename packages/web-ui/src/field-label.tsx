/** Marker is separate from the label: native required semantics supply its name. */
export function FieldLabel({
  id,
  label,
  required,
}: {
  id: string;
  label: string;
  required?: boolean | undefined;
}) {
  return (
    <div className="field-label">
      <label htmlFor={id}>{label}</label>
      {required && <span aria-hidden="true">*</span>}
    </div>
  );
}
