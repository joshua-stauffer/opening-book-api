# API Base for openingbook.org
<p>
  Opening Book is an educational project which allows users to create and study their chess opening repertoire.
  It utilizes the SuperMemo2 algorithm (also used by Anki) in order to prioritize which position is most important to study next.
  There are several modes of study:
</p>
<ul>
  <li>
    <p>Explore: See all book moves (drawn from 1.5M masters games) for a given position, and add moves to your book lines.</p>
  </li>
  <li>
    <p>Play: Play your book lines from beginning to end. Computer chooses the opponent moves that result in positions you know least</p>
  </li>
  <li>
    <p>Study: Get quizzed on the most urgent positions across your opening repertoire.</p>
  </li>
  </ul>
  <p>This Flask powered API is complemented by a ReactJS front-end which draws heavily on chessground and chess.js.</p>
