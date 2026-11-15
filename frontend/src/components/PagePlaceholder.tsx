type Props = {
  title: string
  /** 화면시안·기능 명세에서 이 화면에 들어갈 기능 */
  features: string[]
}

/** 아직 구현 전인 화면. 구현하면서 실제 화면으로 교체한다. */
export function PagePlaceholder({ title, features }: Props) {
  return (
    <section className="panel stack">
      <div className="spread">
        <h2>{title}</h2>
        <span className="chip warn">구현 전</span>
      </div>
      <ul>
        {features.map((f) => (
          <li key={f}>{f}</li>
        ))}
      </ul>
    </section>
  )
}
